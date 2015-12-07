import numpy as np
from scipy.spatial import KDTree as KDTreeType
from Distance import knnW as knnW_from_kdtree
from util import get_points_array

def W_Contiguity(collection, wtype='rook'):
    WTYPE = wtype.upper()
    if WTYPE not in ['QUEEN', 'ROOK']:
        raise ValueError("wtype must be 'QUEEN' or 'ROOK'")
    WTYPE =['QUEEN', 'ROOK'].index(WTYPE)+1
    
    if not np.all([hasattr(feature, '__geo_interface__') for feature in geoints]):
        try:
            feats = parse_geojson(geoints)['features']
            geoints = [ps.cg.asShape(feature['geometry']) for feature in feats]
        except:
            raise AttributeError("Iterable must admit a '__geo_interface__' method")

    geoints = (feature.__geo_interface__ for feature in geoints)

    try:
        shpdict = {idx:ps.cg.asShape(poly) for idx, poly in enumerate(geoints)}
        pc = ps.cg.shapes.PolygonCollection(shpdict)
        neighs = ps.weights.Contiguity.ContiguityWeightsPolygons(pc)
    except:
        raise NotImplementedError('Contiguity Weights from objects with different dimensionality not supported')
    return ps.W(neighs.w)

def W_Rook(collection):
    return Contiguity(collection, wtype='rook')

def W_Queen(collection):
    return Contiguity(collection, wtype='queen')

def W_Knn(collection, k=2, p=2, ids=None, **kwargs):
    if not isinstance(collection, KDTreeType):
        data = get_points_array(collection)
        kdtree = ps.KDTree(data, **kwargs)
    else:
        kdtree = collection
    return ps.weights.Distance.knnW(kdtree, k=k, p=p, ids=ids)

def _ptW(collection, constructor, **kwargs):
    data = get_points_array(collection)
    return constructor(data, **kwargs)

def W_Kernel(collection, **kwargs):
    return _ptW(collection, ps.weights.Distance.Kernel, **kwargs)

def W_Threshold_Binary(collection, **kwargs):
    return _ptW(collection, ps.weights.Distance.DistanceBand, **kwargs)

def W_Threshold_Continuous(collection, **kwargs):
    if not isinstance(collection, KDTreeType):
        radius = kwargs.pop(radius)
        data = get_points_array(collection)
    

