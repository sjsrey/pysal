ToDo for Wconstructor
=======================

- need to agree on a "target" dataformat, in order to ship a
  `weights_from_iterable(iterable,...)` function, or need to figure out how to
  multi-dispatch it based on type of first argument to `W`. Could be something like:

  ```
  class W(object):
        "a spatial weights constructor"

        def __init__(source, *args, **kwargs):
            elif isinstance(source, types.FileType):
                geojson = get_to_geojson(source, *args, **kwargs)
            elif isinstance(source, str):
                geojson = json.loads(source)
            wtype = kwargs.pop(wtype, 'queen')
            self.__geo_interface__ == geojson
            self.do_weights()
  ```
- Need to figure out how to attach other weights classes:
    - KNN
    - Kernel
    - Threshold
