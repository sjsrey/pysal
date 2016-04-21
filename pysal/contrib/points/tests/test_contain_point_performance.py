import pysal as ps
from pysal.cg.shapes import Polygon
import time
import codecs

time_begin = int(round(time.time() * 1000))

pols = ps.open("data/Huangshan_region.shp")  # read the research region shape file
research_region = pols[0]  # set the first polygon as research polygon
print(len(research_region.vertices))  # pring the points count of research region polygon


poi_file = codecs.open("data/poi_info_huangshan.txt", "r", encoding="UTF-8")
print(poi_file.readline())
line_stampe = 0
count_points_in = 0
count_points_out = 0
for line in poi_file:
    line_stampe += 1
    if(len(line)<5):
        continue
    fields = line.split("\t")
    if(len(fields)!=6):
        continue
    x = float(line.split("\t")[4])
    y = float(line.split("\t")[5])
    if research_region.contains_point((x, y)):
        count_points_in += 1
    else:
        count_points_out += 1

time_end = int(round(time.time() * 1000))

print("finished")
print(count_points_in, count_points_out)
print(time_begin, time_end, time_end - time_begin)

