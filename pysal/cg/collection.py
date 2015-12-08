import numpy as np
import json


def ring_bbox(ring):
    xs = [c[0] for c in ring]
    ys = [c[1] for c in ring]
    return min(xs), min(ys), max(xs), max(ys)


class Geometry(object):
    """
    Abstract Class for PySAL Geometry Types
    """
    def __init__(self, coordinates, bbox=None):
        self.coordinates = coordinates
        self.setbbox(bbox)
        self.type = 'Geometry'

    def __str__(self):
        return self.type + ': ' + str(self.coordinates)

    def __repr__(self):
        return '{0}'.format(object.__repr__(self))

    def getbbox(self):
        return self.__bbox

    def setbbox(self, value):
        if value is None:
            value = self.build_bbox()
        self.__bbox = value
    bbox = property(getbbox, setbbox)

    def build_bbox(self):
        raise NotImplementedError('Must implement in subclass')


class Polygon(Geometry):
    """
    Polygon geometry
    """
    def __init__(self, coordinates):
        """
        Arguments
        ---------
        coordinates: list of lists
                   Each list is a ring. First ring is exterior polygon ring,
                   subsequent rings (if any) are holes
        """
        super(Polygon, self).__init__(coordinates)
        self.type = 'Polygon'

    def __str__(self):
        nrings = len(self.coordinates)
        nholes = nrings - 1
        return '{0}: {1} Rings, {2} Holes'.format(self.type, nrings, nholes)

    def build_bbox(self):
        x0 = np.Infinity
        y0 = np.Infinity
        x1 = -np.Infinity
        y1 = -np.Infinity
        self.bboxes = []
        for r, ring in enumerate(self.coordinates):
            l, b, r, t = ring_bbox(ring)
            self.bboxes.append([l, b, r, t])
            x0 = min(l, x0)
            y0 = min(b, y0)
            x1 = max(r, x1)
            y1 = max(t, y1)
        return [x0, y0, x1, y1]




class MultiPolygon(Geometry):
    """
    MultiPolygon geometry

    """
    def __init__(self, coordinates):
        """
        Arguments
        ---------
        coordinates: list of Polygon coordinates
        """
        super(MultiPolygon, self).__init__(coordinates)
        self.type = 'MultiPolygon'

    def __str__(self):
        npolygons = len(self.coordinates)
        return '{0}: {1} Polygon(s)'.format(self.type, npolygons)

    def build_bbox(self):
        x0 = y0 = np.Infinity
        x1 = y1 = -np.Infinity
        self.bboxes = []
        for p, polygon in enumerate(self.coordinates):
            pbbox = []
            for r, ring in enumerate(polygon):
                l, b, r, t = ring_bbox(ring)
                pbbox.append([l, b, r, t])
                x0 = min(l, x0)
                y0 = min(b, y0)
                x1 = max(r, x1)
                y1 = max(t, y1)
            self.bboxes.append(pbbox)
        return [x0, y0, x1, y1]


class LineString(Geometry):
    def __init__(self, coordinates):
        super(LineString, self).__init__(coordinates)
        self.type = "LineString"

    def build_bbox(self):
        return ring_bbox(self.coordinates)


class MultiLineString(Geometry):
    def __init__(self, coordinates):
        super(MultiLineString, self).__init__(coordinates)
        self.type = "MultiLineString"

    def build_bbox(self):
        x0 = y0 = np.Infinity
        x1 = y1 = -np.Infinity
        for lineString in self.coordinates:
            l, b, r, t = LineString(lineString).bbox
            x0 = min(l, x0)
            y0 = min(b, y0)
            x1 = max(r, x1)
            y1 = max(t, y1)
        return [x0, y0, x1, y1]


class Point(Geometry):
    def __init__(self, coordinates):
        super(Point, self).__init__(coordinates)
        self.type = "Point"

    def build_bbox(self):
        return self.coordinates


class MultiPoint(Geometry):
    def __init__(self, coordinates):
        super(MultiPoint, self).__init__(coordinates)
        self.type = "MultiPoint"

    def build_bbox(self):
        # assume all points have same number of coordinates
        m = np.array([point for point in self.coordinates])
        minc = m.min(axis=0).tolist()
        maxc = m.max(axis=0).tolist()
        return minc+maxc

geometryDispatcher = {}
geometryDispatcher[u'Point'] = Point
geometryDispatcher[u'Polygon'] = Polygon
geometryDispatcher[u'LineString'] = LineString
geometryDispatcher[u'MultiPoint'] = MultiPoint
geometryDispatcher[u'MultiPolygon'] = MultiPolygon
geometryDispatcher[u'MultiLineString'] = MultiLineString


class FeatureCollection(object):
    def __init__(self, file_path):
        with open(file_path) as source:
            data = json.load(source)
        features = {}
        self.n_features = 0
        for i, feature in enumerate(data['features']):
            ft = feature['geometry']['type']
            fc = feature['geometry']['coordinates']
            f = {}
            f['geometry'] = geometryDispatcher[ft](fc)
            f['properties'] = feature['properties']
            features[i] = f
            self.n_features += 1
        self.features = features

    def getPropertyTypes(self):
        propertyTypes = {}
        for key in self.features[0]['properties']:
            propertyTypes[key] = type(self.features[0]['properties'][key])
        return propertyTypes

    def getPropertiesAsLists(self, properties):
        a = []
        for i in xrange(self.n_features):
            f = self.features[i]['properties']
            a.append([f[p] for p in properties])
        return a

    def getPropertiesAsArray(self, properties):
        return np.array(self.getPropertiesAsLists(properties))

    def getGeometryCollection(self):
        sf = self.features
        return (sf[f]['geometry'].coordinates for f in sf)

