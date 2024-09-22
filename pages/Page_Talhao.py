import streamlit as st
import geemap.foliumap as geemap
import geopandas as gpd
from zipfile import ZipFile
import os
import ee
import geojson
import json
from shapely import wkb
from shapely.geometry import Polygon
from shapely.geometry import *

try:
    from pages.dev.mvp_functions import remove_third_dimension, talhonamento_classificacao
except:
    pass

st.header("First Map MVP - KMZ/KML Upload")

# Cria o mapa com a camada de satélite
Map = geemap.Map()

# Centraliza o mapa na coordenada inicial (-51.68, -16.3) com zoom 8
Map.setCenter(-51.68, -16.3, 4)

# Criação dos widgets para seleção de parâmetros
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=None)

with col2:
    end_date = st.date_input("End Date", value=None)
cloud_cover = st.slider("Max Cloud Cover (%)", 0, 100, 10)

uploaded_file = st.file_uploader("Faça upload de um arquivo KML ou KMZ", type=["kmz", "kml"])

# Botão para atualizar a imagem
if st.button("Atualizar Imagem"):


    gdf = None  # Inicializamos gdf como None

    if uploaded_file is not None:

        if uploaded_file.name.endswith(".kmz"):
            # Salva o arquivo KMZ temporariamente
            with open("uploaded_file.kmz", "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Extrai o KMZ (que é um arquivo zip) para obter o KML
            with ZipFile("uploaded_file.kmz", "r") as zip_ref:
                zip_ref.extractall("temp_kml")

            # Localiza o arquivo KML extraído
            for file in os.listdir("temp_kml"):
                if file.endswith(".kml"):
                    kml_file = os.path.join("temp_kml", file)
                    gdf = gpd.read_file(kml_file)

        elif uploaded_file.name.endswith(".kml"):
            # Salva o arquivo KML temporariamente
            with open("uploaded_file.kml", "wb") as f:
                f.write(uploaded_file.getbuffer())
            kml_file = "uploaded_file.kml"
            gdf = gpd.read_file(kml_file)

        ########## GDF WORK
        gdf['geometry'] = gdf['geometry'].apply(remove_third_dimension)
        
        fc_roi = gdf.__geo_interface__
        geojson_obj = geojson.loads(json.dumps(fc_roi))
        roi = ee.FeatureCollection(geojson_obj)

        ################### EE WORK
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # Carregar a coleção de imagens do Sentinel-2
        collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(roi) \
            .filterDate(start_date_str, end_date_str) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_cover))\
            .first()\
            .select(['B4', 'B3', 'B2'])
        
        Map.add_basemap('SATELLITE')
        Map.addLayer(collection, {'min': 0, 'max': 3000}, "Sentinel RGB")

        ee_centroid = roi.geometry().centroid()
        Map.center_object(ee_centroid, zoom=15)


        talhao = talhonamento_classificacao(collection, roi)

        # Verifica se as geometrias são válidas
        gdf = gdf[gdf.is_valid]

        # Calcula o centróide das geometrias
        centroid = gdf.geometry.centroid
        centroid_lon, centroid_lat = centroid.x.mean(), centroid.y.mean()

        # Adiciona a camada KML ao mapa
        Map.add_kml(kml_file)
        Map.addLayer(talhao)
        

        # Centraliza o mapa no centróide da geometria com zoom 12
        Map.setCenter(centroid_lon, centroid_lat, 12)

        # Exibe uma mensagem de sucesso
        msg_succ = f"Arquivo carregado! Coordenadas: {centroid_lat} - {centroid_lon}"
        st.success(msg_succ)
        
        # Opcional: Exibe o GeoDataFrame no Streamlit
        st.write(gdf)

    # Exibe o mapa no Streamlit
    Map.to_streamlit(height=600)



    # Remove arquivos temporários após o uso
    if os.path.exists("uploaded_file.kmz"):
        os.remove("uploaded_file.kmz")
    if os.path.exists("uploaded_file.kml"):
        os.remove("uploaded_file.kml")
    if os.path.exists("temp_kml"):
        for file in os.listdir("temp_kml"):
            os.remove(os.path.join("temp_kml", file))
        os.rmdir("temp_kml")
