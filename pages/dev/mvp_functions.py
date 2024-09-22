import ee
from shapely.geometry import *

def remove_third_dimension(geom):
    if geom.is_empty:
        return geom

    if isinstance(geom, Polygon):
        exterior = geom.exterior
        new_exterior = remove_third_dimension(exterior)

        interiors = geom.interiors
        new_interiors = []
        for int in interiors:
            new_interiors.append(remove_third_dimension(int))

        return Polygon(new_exterior, new_interiors)

    elif isinstance(geom, LinearRing):
        return LinearRing([xy[0:2] for xy in list(geom.coords)])

    elif isinstance(geom, LineString):
        return LineString([xy[0:2] for xy in list(geom.coords)])

    elif isinstance(geom, Point):
        return Point([xy[0:2] for xy in list(geom.coords)])

    elif isinstance(geom, MultiPoint):
        points = list(geom.geoms)
        new_points = []
        for point in points:
            new_points.append(remove_third_dimension(point))

        return MultiPoint(new_points)

    elif isinstance(geom, MultiLineString):
        lines = list(geom.geoms)
        new_lines = []
        for line in lines:
            new_lines.append(remove_third_dimension(line))

        return MultiLineString(new_lines)

    elif isinstance(geom, MultiPolygon):
        pols = list(geom.geoms)

        new_pols = []
        for pol in pols:
            new_pols.append(remove_third_dimension(pol))

        return MultiPolygon(new_pols)

    elif isinstance(geom, GeometryCollection):
        geoms = list(geom.geoms)

        new_geoms = []
        for geom in geoms:
            new_geoms.append(remove_third_dimension(geom))

        return GeometryCollection(new_geoms)

    else:
        raise RuntimeError("Currently this type of geometry is not supported: {}".format(type(geom)))



def atribuir_idgrid(feature, idgrid):
    return feature.set({'idgrid': idgrid})

def talhonamento_classificacao(image, roi):
    # Recorte a imagem usando a máscara de agricultura
    imagem_substituidaComMascara = image.clip(roi)

    # Seção de segmentação -----------------------------------------------------------------------------

    # Crie as sementes para a segmentação
    seeds = ee.Algorithms.Image.Segmentation.seedGrid(50)

    # Realize a segmentação usando o algoritmo SNIC
    snic = ee.Algorithms.Image.Segmentation.SNIC(
        image = imagem_substituidaComMascara.select('B4'),
        compactness=0,
        connectivity=4,
        neighborhoodSize=20,
        size=20,
        seeds=seeds
    )

    # Selecione a banda 'clusters' da saída da segmentação
    clusters_snic = snic.select("clusters")

    # Reduza os clusters para vetores usando a função reduceToVectors
    vectors_colheita = clusters_snic.reduceToVectors(
        geometryType='polygon',
        reducer=ee.Reducer.countEvery(),
        scale=20,
        maxPixels=1e13,
        geometry=roi
    )

    return vectors_colheita
