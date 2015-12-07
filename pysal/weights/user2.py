import numpy as np
from scipy.spatial import KDTree, cKDTree
from pysal.cg.kdtree import Arc_KDTree
from Distance import knnW as knnW_from_kdtree
import util
import pysal as ps

KDTreeTypes = [KDTree, cKDTree, Arc_KDTree]

def _W_Contiguity(collection, wtype='rook', **kwargs):
    """
    Arbitrary contiguity constructor from an iterable of polygons
    """
    WTYPE = wtype.upper()
    if WTYPE not in ['QUEEN', 'ROOK']:
        raise ValueError("wtype must be 'QUEEN' or 'ROOK'")
    WTYPE =['QUEEN', 'ROOK'].index(WTYPE)+1
    try:
        pc = ps.cg.shapes.asPolygonCollection(collection, **kwargs)
    except TypeError:
        raise Exception("could not convert collection to PolygonCollection")
    neighs = ps.weights.Contiguity.ContiguityWeightsPolygons(pc, wttype=WTYPE)
    return ps.W(neighs.w)

def W_Rook(collection):
    """
    Specific rook contiguity constructor from an iterable of polygons
    """
    return _W_Contiguity(collection, wtype='rook')

def W_Queen(collection):
    """
    Specific queen contiguity constructor from an iterable of polygons
    """
    return _W_Contiguity(collection, wtype='queen')

def W_Knn(collection, **kwargs):
    """
    K-nearest neighbors constructor from a container of points
    """
    return _ptW(collection, ps.weights.Distance.knnW, **kwargs)

def _ptW(collection, constructor, *args, **kwargs):
    data = util.get_points_array(collection)
    return constructor(data, *args, **kwargs)

def W_Kernel(collection, **kwargs):
    return _ptW(collection, ps.weights.Distance.Kernel, **kwargs)

def W_Kernel_Adaptive(collection, *args, **kwargs):
    kwargs['fixed'] = False
    return _ptW(collection, ps.weights.Distance.Kernel, *args, **kwargs) 

def W_Threshold_Binary(collection, *args, **kwargs):
    return _ptW(collection, ps.weights.Distance.DistanceBand, *args, **kwargs)

def W_Threshold_Continuous(collection, *args, **kwargs):
    kwargs['binary'] = False
    return _ptW(collection, ps.weights.Distance.DistanceBand, *args, **kwargs)
