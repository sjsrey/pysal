def asPolygonCollection(collection, **kwargs):
    """
    Construct a PolygonCollection from an arbitrary iterable of shapes.
    """
    ids = kwargs.pop('ids', None)
    if ids is None:
        ids = ()
    if isinstance(collection, PolygonCollection):
        out = collection
    elif isinstance(collection, dict):
        #if we have a standardized geojson handler, then we could check if this
        #is geojson FeatureCollection or GeometryCollection and pass the handler
        collection = {k:asShape(v) for k,v in diter(collection)}
        out = PolygonCollection(collection, **kwargs)
    else:
        try:
            collection = {i:asShape(v) for i,v in enumerate(collection)}
        except TypeError:
            raise TypeError("collection is not iterable")
        out = PolygonCollection(collection, **kwargs)
    return out

def asShape(obj):
    """
    Returns a pysal shape object from obj.
    obj must support the __geo_interface__.
    """
    if type(obj) in _geoJSON_type_to_Pysal_type.values():
        return obj #already pysal object
    if hasattr(obj, '__geo_interface__'):
        geo = obj.__geo_interface__
    else:
        geo = obj
    if hasattr(geo, 'type'):
        raise TypeError('%r does not appear to be a shape object' % (obj))
    geo_type = geo['type'].lower()
    #if geo_type.startswith('multi'):
    #    raise NotImplementedError, "%s are not supported at this time."%geo_type
    if geo_type in _geoJSON_type_to_Pysal_type:
        return _geoJSON_type_to_Pysal_type[geo_type].__from_geo_interface__(geo)
    else:
        raise NotImplementedError(
            "%s is not supported at this time." % geo_type)
