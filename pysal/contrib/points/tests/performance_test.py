# Import essential libraries for following calculation
import sys
path_base_dell = 'C:/work/ASUWork/pysal'
path_base_lenove = 'D:/ASUWork/pysal'
path_base_os = '/Users/hushao/Documents/ASUWork/pysal/'
sys.path.append(path_base_dell)
sys.path.append(path_base_lenove)
sys.path.append(path_base_os)
import pysal as ps
import numpy as np
from pysal.contrib.points.pointpattern import PointPattern
from pysal.contrib.points.process import PoissonPointProcess
from pysal.contrib.points.distance_statistics import G, F, J, K, L
from pysal.contrib.points.distance_statistics import Genv, Fenv, Jenv, Kenv, Lenv
from test_contain_point_performance import Cell, ZonalStructure
import matplotlib.pyplot as plt
import time
import codecs
import shapely
# from pysal.cg.shapes import Polygon, Point
# from shapely.geometry import Polygon, Point
import time
print("import finished!")


def data_praparing(point_file_name, boundary_sample_step = 1, point_sample_step = 1):
    """
    point_file_name could be "poi" or "weibo"
    """
    polygons = ps.open("data/Huangshan_region.shp")  # read the research region shape file
    research_region = polygons[0]  # set the first polygon as research polygon
#     print(str.format("Polygon read, vertices number = {}", len(research_region.vertices)))
    file_name = ''
    fields_limit = 5
    index_x = 0
    index_y = 0
    if point_file_name == "poi":
        file_name = "poi_info_huangshan.txt"
        fields_limit = 6
        index_x = 4
        index_y = 5
    elif point_file_name == "weibo":
        file_name = "geoweibo_huangshan_only.txt"
        fields_limit = 5
        index_x = 2
        index_y = 3
    point_file = codecs.open("data/"+file_name, "r", encoding="UTF-8")
    point_file.readline()
    points = []
    for line in point_file:
        if(len(line)<5):
            continue
        fields = line.split("\t")
        if(len(fields)!=fields_limit):
            continue
        x = float(line.split("\t")[index_x])
        y = float(line.split("\t")[index_y])
        points.append([x, y])
    result = (research_region.vertices, points)
    point_file.close()
    if boundary_sample_step != 1:
        simple_boundary = []
        for i in xrange(0, len(result[0])-1, boundary_sample_step):
            simple_boundary.append(result[0][i])
        simple_boundary.append(result[0][len(result[0])-1])
        result = (simple_boundary, result[1])
    if point_sample_step != 1:
        simple_points = []
        for i in xrange(0, len(result[1]), point_sample_step):
            simple_points.append(result[1][i])
        result = (result[0], simple_points)
    return result

# data = data_praparing("poi")

def test_pysal(data):
    count_points_in = 0
    count_points_out = 0
    polygon = ps.cg.shapes.Polygon(data[0])
    for point in data[1]:
        if polygon.contains_point(point):
            count_points_in += 1
        else:
            count_points_out += 1
    # print(str.format("finished, points in = {}; points out = {}", count_points_in, count_points_out))

def test_shapely(data):
    count_points_in = 0
    count_points_out = 0
    polygon = shapely.geometry.Polygon(data[0])
    for point in data[1]:
        if polygon.contains(shapely.geometry.Point(point[0], point[1])):
            count_points_in += 1
        else:
            count_points_out += 1
    # print(str.format("finished, points in = {}; points out = {}", count_points_in, count_points_out))

def test_quadtree(data):
    count_points_in = 0
    count_points_out = 0
    zonal_structure = ZonalStructure(ps.cg.shapes.Ring(data[0]))
    for point in data[1]:
        if zonal_structure.contains_point(point):
            count_points_in += 1
        else:
            count_points_out += 1
    # print(str.format("finished, points in = {}; points out = {}", count_points_in, count_points_out))


#  begin the test
f_result = open("compare_result.txt", "w")

# 1. fix the boundary number, vary the points number
line = ", ".join(["point_size", "pysal", "shapely", "quadtree"])
print(line)
f_result.write(line+"\n")
for step in [10000, 5000, 2000, 1000, 800, 500, 200, 100, 80, 50, 30, 20, 10, 5, 1]:
    data = data_praparing("weibo", 1, step)
    time_pysal = 0
    time_shapely = 0
    time_quadtree = 0
    for type in ["pysal", "shapely", "quadtree"]:
        time_begin = int(round(time.time() * 1000))
        count_points_in = 0
        count_points_out = 0
        if type == "pysal":
            test_pysal(data)
            time_end = int(round(time.time() * 1000))
            time_pysal = time_end - time_begin
        elif type == "shapely":
            test_shapely(data)
            time_end = int(round(time.time() * 1000))
            time_shapely = time_end - time_begin
        elif type == "quadtree":
            test_quadtree(data)
            time_end = int(round(time.time() * 1000))
            time_quadtree = time_end - time_begin
    line = ", ".join(map(str, [len(data[1]), time_pysal, time_shapely, time_quadtree]))
    print(line)
    f_result.write(line+"\n")
    f_result.flush()


# 2. fix the points number, vary the boundary number
print("------------------------------------------------------")
f_result.write("------------------------------------------------------\n")

line = ", ".join(["boundary_point_size", "pysal", "shapely", "quadtree"])
print(line)
f_result.write(line+"\n")
for step in [500, 300, 100, 80, 50, 30, 20, 10, 5, 1]:
    data = data_praparing("poi", step, 1)
    time_pysal = 0
    time_shapely = 0
    time_quadtree = 0
    for type in ["pysal", "shapely", "quadtree"]:
        time_begin = int(round(time.time() * 1000))
        count_points_in = 0
        count_points_out = 0
        if type == "pysal":
            test_pysal(data)
            time_end = int(round(time.time() * 1000))
            time_pysal = time_end - time_begin
        elif type == "shapely":
            test_shapely(data)
            time_end = int(round(time.time() * 1000))
            time_shapely = time_end - time_begin
        elif type == "quadtree":
            test_quadtree(data)
            time_end = int(round(time.time() * 1000))
            time_quadtree = time_end - time_begin
    line = ", ".join(map(str, [len(data[0]), time_pysal, time_shapely, time_quadtree]))
    print(line)
    f_result.write(line+"\n")
    f_result.flush()

print("finished!")
f_result.close()
