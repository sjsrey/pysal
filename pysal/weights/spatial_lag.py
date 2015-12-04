"""
Spatial lag operations.
"""
__author__ = "Sergio J. Rey <srey@asu.edu>, David C. Folch <david.folch@asu.edu>"
__all__ = ['lag_spatial']
import numpy as np
from collections import Counter
from six import iteritems as diter

def lag_spatial(w, y):
    """
    Spatial lag operator.

    If w is row standardized, returns the average of each observation's neighbors;
    if not, returns the weighted sum of each observation's neighbors.

    Parameters
    ----------

    w                   : W
                          PySAL spatial weights object
    y                   : array
                          numpy array with dimensionality conforming to w (see examples)

    Returns
    -------

    wy                  : array
                          array of numeric values for the spatial lag

    Examples
    --------

    Setup a 9x9 binary spatial weights matrix and vector of data; compute the
    spatial lag of the vector.

    >>> import pysal
    >>> import numpy as np
    >>> w = pysal.lat2W(3, 3)
    >>> y = np.arange(9)
    >>> yl = pysal.lag_spatial(w, y)
    >>> yl
    array([  4.,   6.,   6.,  10.,  16.,  14.,  10.,  18.,  12.])

    Row standardize the weights matrix and recompute the spatial lag

    >>> w.transform = 'r'
    >>> yl = pysal.lag_spatial(w, y)
    >>> yl
    array([ 2.        ,  2.        ,  3.        ,  3.33333333,  4.        ,
            4.66666667,  5.        ,  6.        ,  6.        ])

    Explicitly define data vector as 9x1 and recompute the spatial lag

    >>> y.shape = (9, 1)
    >>> yl = pysal.lag_spatial(w, y)
    >>> yl
    array([[ 2.        ],
           [ 2.        ],
           [ 3.        ],
           [ 3.33333333],
           [ 4.        ],
           [ 4.66666667],
           [ 5.        ],
           [ 6.        ],
           [ 6.        ]])

    Take the spatial lag of a 9x2 data matrix

    >>> yr = np.arange(8, -1, -1)
    >>> yr.shape = (9, 1)
    >>> x = np.hstack((y, yr))
    >>> yl = pysal.lag_spatial(w, x)
    >>> yl
    array([[ 2.        ,  6.        ],
           [ 2.        ,  6.        ],
           [ 3.        ,  5.        ],
           [ 3.33333333,  4.66666667],
           [ 4.        ,  4.        ],
           [ 4.66666667,  3.33333333],
           [ 5.        ,  3.        ],
           [ 6.        ,  2.        ],
           [ 6.        ,  2.        ]])

    """
    return w.sparse * y

def lag_categorical(w, y, ties='tryself'):
    """
    Constructs the most common categories of neighboring observations, weighted
    by their weight strength. 
    
    Parameters
    ----------

    w                   : W
                          PySAL spatial weightsobject
    y                   : iterable
                          iterable collection of categories (either int or
                          string) with dimensionality conforming to w (see examples)
    ties                : str
                          string describing the method to use when resolving
                          ties. By default, the option is "tryself",
                          and the category of the focal observation 
                          is included with its neighbors to try
                          and break a tie. If this does not resolve the tie,
                          a winner is chosen randomly. To just use random choice to
                          break ties, pass "random" instead.
    Returns
    -------
    an (n x 1) column vector containing the most common neighboring observation
    """
    if isinstance(y, list):
        y = np.array(y)
    y = y.flatten()
    output = np.zeros_like(y)
    keys = np.unique(y)
    #ints = np.arange(len(keys))
    inty = np.zeros(y.shape, dtype=np.int)
    for i,key in enumerate(keys):
       inty[y == key] = i 
    for idx,neighbors in w:
        vals = np.zeros(keys.shape)
        #not sure how to vectorize when some neighbors are in the same class.
        #I was trying
        #vals[inty[neighbors.keys()]] += neighbors.values()
        for neighb, weight in diter(neighbors):
            vals[inty[neighb]] += weight
        outidx = _resolve_ties(idx,inty,vals,neighbors,ties)
        output[w.id2i[idx]] = keys[outidx]
    return output.reshape(len(y),1)

def _resolve_ties(i,inty,vals,neighbors,method):
    if len(vals[vals==vals.max()]) <= 1:
        return np.argmax(vals)
    elif method.lower() == 'random':
        ties = np.where(vals == vals.max())
        return np.random.choice(vals[ties])
    elif method.lower() == 'tryself':
        print(vals,i)
        vals[inty[i]] += np.mean(neighbors.values())
        print(vals,i)
        return _resolve_ties(i,inty,vals,neighbors,'random')

