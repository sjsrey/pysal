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


class Cell():
    """
    Basic rectangle geometry used for dividing research area (polygon) into quadtree structure
    Attributes
    --------------
    level       : int
                  on which quadtree level this cell belongs to. Begins with 0
    index_h     : int
                  the vertical index of this cell in current level
    index_v     : int
                  the vertical index of this cell in current level
    min_x       : float
                  min x coordinate of this cell
    min_y       : float
                  min y coordinate of this cell
    length_x    : float
                  width of this cell
    length_y    : float
                  height of this cell
    arcs        : list
                  detected arc list which are within this cell
    status      : str
                  enum status of this cell, indicating this cell's spatial relationship with the research area
                  "in"      : this cell lies totally inside of the research area
                  "out"     : this cell lies totally outside of the research area
                  "maybe"   : this cell intersects with the research area's boundary
    """

    def __init__(self, level, index_h, index_v, min_x, min_y, length_x, length_y, arcs, status):
        """

        Parameters
        ----------
        level       : int
                      on which quadtree level this cell belongs to. Begins with 0
        index_h     : int
                      the vertical index of this cell in current level
        index_v     : int
                      the vertical index of this cell in current level
        min_x       : float
                      min x coordinate of this cell
        min_y       : float
                      min y coordinate of this cell
        length_x    : float
                      width of this cell
        length_y    : float
                      height of this cell
        arcs        : list
                      detected arc list which are within this cell
        status      : str
                      enum status of this cell, indicating this cell's spatial relationship with the research area
                      "in"      : this cell lies totally inside of the research area
                      "out"     : this cell lies totally outside of the research area
                      "maybe"   : this cell intersects with the research area's boundary
        """
        self.level = level
        self.index_h = index_h
        self.index_v = index_v
        self.min_x = min_x
        self.min_y = min_y
        self.length_x = length_x
        self.length_y = length_y
        self.arcs = arcs
        self.status = status

    def split(self):
        """
        equally split current cell into 4 sub cells
        Returns
        -------
        the list of 4 sub cells
        """
        sub_cells = []
        if self.status == "in" or self.status == "out": # no need to intersect with the arcs, the sub cells will inherit the status of this cell
            level = self.level + 1
            index_h = self.index_h * 2
            index_v = self.index_v * 2
            length_x = self.length_x / 2
            length_y = self.length_y / 2
            # create the cell on left-bottom, right-bottom, left-top and right-top
            cells_l_b = Cell(level, index_h, index_v, self.min_x, self.min_y, length_x, length_y, [], self.status)
            cells_r_b = Cell(level, index_h+1, index_v, self.min_x+length_x, self.min_y, length_x, length_y, [], self.status)
            cells_l_t = Cell(level, index_h, index_v+1, self.min_x, self.min_y+length_y, length_x, length_y, [], self.status)
            cells_r_t = Cell(level, index_h+1, index_v+1, self.min_x+length_x, self.min_y+length_y, length_x, length_y, [], self.status)
            sub_cells = [cells_l_b, cells_r_b, cells_l_t, cells_r_t]
        else:
            """
            Do the real and important split work here.
            Some properties of the arc:
            - Point order of the arcs MUST be clockwise
            - The two end-points of each arc MUST lie on the borders of the cell
            - When a arc goes in a cell, it MUST goes out from the same one
            - The intersection points MUST be lying on the inner-boundaries which are used to divide the cell into 4 sub-cells
            - Use the intersection points to split the arcs into small ones
            - No need to store cell boundaries as arcs, store the intersection points, points' relative location from
            """
            sub_cells = []

        return  sub_cells