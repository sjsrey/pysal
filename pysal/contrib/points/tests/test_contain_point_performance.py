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
                  the horizontal index of this cell in current level
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
                      the horizontal index of this cell in current level
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
        level = self.level + 1
        index_h = self.index_h * 2
        index_v = self.index_v * 2
        length_x = self.length_x / 2
        length_y = self.length_y / 2
        if self.status == "in" or self.status == "out": # no need to intersect with the arcs, the sub cells will inherit the status of this cell
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
            if self.level == 0:
                if len(self.arcs) != 1:
                    raise  LookupError(
                        "Unexpected arc number! Holes are not supported currently"
                    )
                    return []
                # Do some initialize work, find one point at the edge of the polygon(study area) and begin with this point
                arc = self.arcs[0]
                if arc[0] ==  arc[len(arc)-1]:  # remove the duplicated points the the end of the arc
                    arc = arc[0: len(arc)-1]
                min_x = arc[0][0]
                min_x_index = 0
                for index in range(0, len(arc)):
                    if arc[index][0] < min_x:
                        min_x = arc[index][0]
                        min_x_index = index
                arc = arc[min_x_index: len(arc)] + arc[0: min_x_index+1]
                self.arcs[0] = arc

                # now begin comparing each segment of the arc to the split line (horizontal and)
                split_line_h = [[self.min_x, self.min_y+length_y], [self.min_x+self.length_x, self.min_y+length_y]]
                split_line_v = [[self.min_x+length_x, self.min_y], [self.min_x+length_x, self.min_y+self.length_y]]
                # l: left, r: right, b: bottom, t: top
                cell_arcs_l_b = []
                cell_arcs_r_b = []
                cell_arcs_l_t = []
                cell_arcs_r_t = []
                for arc in self.arcs:
                    temp_arc = []
                    temp_arc_belonging = None
                    for index in range(0, len(arc)-1):
                        x0 = arc[index][0]
                        y0 = arc[index][1]
                        x1 = arc[index+1][0]
                        y1 = arc[index+1][1]
                        if temp_arc_belonging == None:
                            """
                            In this section, determine which sub-cell does the current temp_arc belong to
                            As we mentioned, each single arc MUST begin and end at the boundary line of the cell,
                            So, at the beginning, we need to decide the status according to the start point's
                            position on cell boundary line.
                            However, once the split-of-arc begin, next arc's belonging sub-cell can be determined by the
                            previous'
                            See the image cell_boundary_category_rule to better understand the process
                            """
                            if x0 == self.min_x:
                                if y0 < self.min_y + length_y:  # position 1
                                    temp_arc_belonging = "l_b"
                                elif y0 > self.min_y + length_y:  # position 2
                                    temp_arc_belonging = "l_t"
                                else:  # just by chance at the middle point
                                    if y1 < y0:  # going down
                                        temp_arc_belonging = "l_b"
                                    elif y1 > y0:  # going up
                                        temp_arc_belonging = "l_t"
                                    else: # just by chance this segment lies on split_line_h, throw it
                                        continue
                            elif x[0] == self.min_x+self.length_x:
                                if y0 < self.min_y + length_y:  # position 6
                                    temp_arc_belonging = "r_b"
                                elif y0 > self.min_y + length_y:  # position 5
                                    temp_arc_belonging = "r_t"
                                else:  # just by chance at the middle point
                                    if y1 < y0:  # going down
                                        temp_arc_belonging = "r_b"
                                    elif y1 > y0:  # going up
                                        temp_arc_belonging = "r_t"
                                    else:  # just by chance this segment lies on split_line_h, throw it
                                        continue
                            elif y0 == self.min_y:
                                if x0 < self.min_x + length_x: # position 8
                                    temp_arc_belonging = "l_b"
                                elif x0 > self.min_x + length_x: # position 7
                                    temp_arc_belonging = "r_b"
                                else:  # just by chance at the middle point
                                    if x1 < x0:  # going left
                                        temp_arc_belonging = "l_b"
                                    elif x1 > x0:  #going right
                                        temp_arc_belonging = "r_b"
                                    else:   # just by chance this segment lies on split_line_v, throw it
                                        continue
                            else:  # in which situation, y0 == self.min_y+self.length_y:
                                if x0 < self.min_x + length_x:  # position 3
                                    temp_arc_belonging = "l_t"
                                elif x0 > self.min_x + length_x:  # position 4
                                    temp_arc_belonging = "r_t"
                                else:  # just by chance at the middle point
                                    if x1 < x0:  # going left
                                        temp_arc_belonging = "l_t"
                                    elif x1 > x0:  # going right
                                        temp_arc_belonging = "r_t"
                                    else:  # just by chance this segment lies on split_line_v, throw it
                                        continue
                        # At this point, the belonging sub-cell of current segment is already known.
                        # Let's begin the splitting!
                        # determine if the segment intersects with split_line_h





        return  sub_cells