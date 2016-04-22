import pysal as ps
from pysal.cg.shapes import Polygon
import time
import codecs
import math

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


class Cell(object):
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
        middle_x = self.min_x + length_x
        middle_y = self.min_y + length_y
        if self.status == "in" or self.status == "out": # no need to intersect with the arcs, the sub cells will inherit the status of this cell
            # create the cell on left-bottom, right-bottom, left-top and right-top
            cells_l_b = Cell(level, index_h, index_v, self.min_x, self.min_y, length_x, length_y, [], self.status)
            cells_r_b = Cell(level, index_h+1, index_v, middle_x, self.min_y, length_x, length_y, [], self.status)
            cells_l_t = Cell(level, index_h, index_v+1, self.min_x, middle_y, length_x, length_y, [], self.status)
            cells_r_t = Cell(level, index_h+1, index_v+1, middle_x, middle_y, length_x, length_y, [], self.status)
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
            if self.level == 0:
                if len(self.arcs) != 1:
                    raise LookupError(
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
                split_line_h = [[self.min_x, middle_y], [self.min_x+self.length_x, middle_y]]
                split_line_v = [[middle_x, self.min_y], [middle_x, self.min_y+self.length_y]]
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
                        if temp_arc_belonging is None:
                            """
                            In this section, determine which sub-cell does the current temp_arc belong to
                            Although every single arc must begin and end on the cell's outer boundaries, when the split
                            process begin, there might be some sub-arcs begin at the split-line. So here we should
                            consider all possible situations
                            See the image cell_boundary_category_rule to better understand the process
                            """
                            if x0 == self.min_x:  # left border
                                if y0 < middle_y:  # position 1
                                    temp_arc_belonging = "l_b"
                                elif y0 > middle_y:  # position 2
                                    temp_arc_belonging = "l_t"
                                else:  # just by chance at the middle point
                                    if y1 < y0:  # going down
                                        temp_arc_belonging = "l_b"
                                    elif y1 > y0:  # going up
                                        temp_arc_belonging = "l_t"
                                    else: # just by chance this segment lies on split_line_h, throw it
                                        continue
                            elif x0 == self.min_x+self.length_x:  # right border
                                if y0 < middle_y:  # position 6
                                    temp_arc_belonging = "r_b"
                                elif y0 > middle_y:  # position 5
                                    temp_arc_belonging = "r_t"
                                else:  # just by chance at the middle point
                                    if y1 < y0:  # going down
                                        temp_arc_belonging = "r_b"
                                    elif y1 > y0:  # going up
                                        temp_arc_belonging = "r_t"
                                    else:  # just by chance this segment lies on split_line_h, throw it
                                        continue
                            elif y0 == self.min_y:  # bottom border
                                if x0 < middle_x: # position 8
                                    temp_arc_belonging = "l_b"
                                elif x0 > middle_x: # position 7
                                    temp_arc_belonging = "r_b"
                                else:  # just by chance at the middle point
                                    if x1 < x0:  # going left
                                        temp_arc_belonging = "l_b"
                                    elif x1 > x0:  #going right
                                        temp_arc_belonging = "r_b"
                                    else:   # just by chance this segment lies on split_line_v, throw it
                                        continue
                            elif y0 == self.min_y+self.length_y:  # top border
                                if x0 < middle_x:  # position 3
                                    temp_arc_belonging = "l_t"
                                elif x0 > middle_x:  # position 4
                                    temp_arc_belonging = "r_t"
                                else:  # just by chance at the middle point
                                    if x1 < x0:  # going left
                                        temp_arc_belonging = "l_t"
                                    elif x1 > x0:  # going right
                                        temp_arc_belonging = "r_t"
                                    else:  # just by chance this segment lies on split_line_v, throw it
                                        continue
                            elif x0 == middle_x:  # split_line_v
                                if y0 > middle_y: # position c
                                    if x1 > x0:
                                        temp_arc_belonging = "r_t"
                                    elif x1 < x0:
                                        temp_arc_belonging = "l_t"
                                    else:  # x1==x0, just by chance on the split_line_v
                                        continue
                                elif y0 < middle_y: # position d
                                    if x1 > x0:
                                        temp_arc_belonging = "r_b"
                                    elif x1 < x0:
                                        temp_arc_belonging = "l_b"
                                    else:  # x1==x0, just by chance on the split_line_v
                                        continue
                                else:  # in condition that p0 lies at the cross point of two split lines
                                    if x1 == x0 or y1 == y0:  # on one of the split_line
                                        continue
                                    elif x1 > x0:
                                        if y1 > y0:
                                            temp_arc_belonging = "r_t"
                                        else:
                                            temp_arc_belonging = "r_b"
                                    else:  # on condition that x1 < x0
                                        if y1 > y0:
                                            temp_arc_belonging = 'l_t'
                                        else:
                                            temp_arc_belonging = "l_b"
                            elif y0 == middle_y:  # split_line_h
                                if x0 > middle_x:  #position b
                                    if y1 > y0:
                                        temp_arc_belonging = "r_t"
                                    elif y1 < y0:
                                        temp_arc_belonging = "r_b"
                                    else:  # y1==y0, just by chance on the split_line_h
                                        continue
                                else:  # on condition that x0 < middle_x, position a
                                    if y1 > y0:
                                        temp_arc_belonging = "l_t"
                                    elif y1 < y0:
                                        temp_arc_belonging = "l_b"
                                    else:  # y1==y0, just by chance on the split_line_h
                                        continue
                        if temp_arc_belonging is None:
                            raise Exception("Error on cell split!!!")

                        # At this point, the belonging sub-cell of current segment is already known.
                        # Let's begin the splitting!
                        """
                        Firstly determine if the segment totally lies on the split_lines.
                        p1 (x1, y1) could lie on the split_lines
                        This situation is not the same with previous ones which "both points lie on the same split_line"
                        In previous situation, the p1 is the begin point of a sub arc, we can just throw that segment if
                        it totally lie on split_line. However, in current situation, the segment is in the middle of the
                        sub-arc. So if the segment is detected totally lie on the split_line, we should split the sub_arc
                        here.
                        """
                        if x0==x1==middle_x or y0==y1==middle_y:  # split the arc here, throw current segment
                            if len(temp_arc)!=0:
                                if temp_arc_belonging == "l_b":
                                    cell_arcs_l_b.append(temp_arc)
                                elif temp_arc_belonging == "l_t":
                                    cell_arcs_l_t.append(temp_arc)
                                elif temp_arc_belonging == "r_b":
                                    cell_arcs_r_b.append(temp_arc)
                                elif temp_arc_belonging == "r_t":
                                    cell_arcs_r_t.append(temp_arc)
                            temp_arc = []
                            temp_arc_belonging = None
                            continue
                        # Check if end point(p2) lies on split_lies, this kind of situation is also easy to handle
                        # split the arc here, but no need to split the segment
                        if x1==middle_x or y1==middle_y:
                            if len(temp_arc) == 0:
                                temp_arc.append([x0, y0])
                            temp_arc.append([x1, y1])
                            if temp_arc_belonging == "l_b":
                                cell_arcs_l_b.append(temp_arc)
                            elif temp_arc_belonging == "l_t":
                                cell_arcs_l_t.append(temp_arc)
                            elif temp_arc_belonging == "r_b":
                                cell_arcs_r_b.append(temp_arc)
                            elif temp_arc_belonging == "r_t":
                                cell_arcs_r_t.append(temp_arc)
                            temp_arc = []
                            temp_arc_belonging = None
                            continue
                        intersect_point_h = None
                        intersect_point_v = None
                        # Check if the segment intersects with split_line_h
                        if (y0 < middle_y < y1) or (y0 > middle_y > y1):
                            if x0 == x1:  # the segments is vertical
                                intersect_point_h = [x0, middle_y]
                            else:
                                a = (y1-y0) / (x1-x0)
                                b = y0 - a*x0
                                x_new = (middle_y-b)/a
                                intersect_point_h = [x_new, middle_y]
                        # Check if the segment intersects with split_line_v
                        if (x0 < middle_x < x1) or (x0 > middle_x > x1):
                            if y0 == y1:  # the segments is horizontal
                                intersect_point_v = [middle_x, y0]
                            else:
                                a = (y1 - y0) / (x1 - x0)
                                b = y0 - a * x0
                                y_new = a*middle_x + b
                                intersect_point_v = [middle_x, y_new]
                        # check if the intersect point(s) exist
                        intersect_point = None
                        intersect_point_mark = None
                        if(intersect_point_h is not None) and (intersect_point_v is not None):
                            # In this situation, the current segment cannot be vertical nor horizontal.
                            # Find the closer intersection point to p0
                            if math.fabs(intersect_point_h[0]-x0)<math.fabs(intersect_point_v[0]-x0):
                                intersect_point = intersect_point_h
                                intersect_point_mark = "h"
                            else:
                                intersect_point = intersect_point_v
                                intersect_point_mark = "v"
                        elif intersect_point_h is not None:
                            intersect_point = intersect_point_h
                            intersect_point_mark = "h"
                        elif intersect_point_v is not None:
                            intersect_point = intersect_point_v
                            intersect_point_mark = "v"

                        if intersect_point is not None:  # split the arc here
                            if len(temp_arc) == 0:
                                temp_arc.append([x0, y0])
                            temp_arc.append(intersect_point)
                            if temp_arc_belonging == "l_b":
                                cell_arcs_l_b.append(temp_arc)
                            elif temp_arc_belonging == "l_t":
                                cell_arcs_l_t.append(temp_arc)
                            elif temp_arc_belonging == "r_b":
                                cell_arcs_r_b.append(temp_arc)
                            elif temp_arc_belonging == "r_t":
                                cell_arcs_r_t.append(temp_arc)
                            # since the segment is broken here, init the next temp_arc
                            temp_arc = [intersect_point, [x1, y1]]
                            if temp_arc_belonging == "l_b":
                                if intersect_point_mark == "h":
                                    temp_arc_belonging = "l_t"
                                else:
                                    temp_arc_belonging = "r_b"

                            elif temp_arc_belonging == "l_t":
                                if intersect_point_mark == "h":
                                    temp_arc_belonging = "l_b"
                                else:
                                    temp_arc_belonging = "r_t"

                            elif temp_arc_belonging == "r_b":
                                if intersect_point_mark == "h":
                                    temp_arc_belonging = "r_t"
                                else:
                                    temp_arc_belonging = "l_b"

                            elif temp_arc_belonging == "r_t":
                                if intersect_point_mark == "h":
                                    temp_arc_belonging = "r_b"
                                else:
                                    temp_arc_belonging = "l_t"
                        else:  # simply append the point to current arc
                            if len(temp_arc) == 0:
                                temp_arc.append([x0, y0])
                            temp_arc.append(intersect_point)
                    # Allocate the last left arc to a sub-cell
                    if len(temp_arc) > 0:
                        if temp_arc_belonging == "l_b":
                            cell_arcs_l_b.append(temp_arc)
                        elif temp_arc_belonging == "l_t":
                            cell_arcs_l_t.append(temp_arc)
                        elif temp_arc_belonging == "r_b":
                            cell_arcs_r_b.append(temp_arc)
                        elif temp_arc_belonging == "r_t":
                            cell_arcs_r_t.append(temp_arc)
                """
                At this point, all the arcs in this cell have been split into sub-arcs and allocated to 4 sub-cells.
                So, we can try to create the cells on left-bottom, right-bottom, left-top and right-top.
                Before doing that, we need to determine the status of each sub-cell, especially those who are totally
                within or out of the study area.
                These two kind of sub-cell have the same property: they don't have arc allocated. So, If here exists
                cell(s) who don't have arcs allocated, we need to begin the check
                """
                if len(cell_arcs_l_b)*len(cell_arcs_l_t)*len(cell_arcs_r_b)*len(cell_arcs_r_t) == 0:
                    if len(cell_arcs_l_b) > 0:
                        point_arc_dict = {}
                        px = self.min_x
                        py = self.min_y
                        for arc in cell_arcs_l_b:


                else:
                    cells_l_b = Cell(level, index_h, index_v, self.min_x, self.min_y, length_x, length_y, [], self.status)
                    cells_r_b = Cell(level, index_h + 1, index_v, middle_x, self.min_y, length_x, length_y, [], self.status)
                    cells_l_t = Cell(level, index_h, index_v + 1, self.min_x, middle_y, length_x, length_y, [], self.status)
                    cells_r_t = Cell(level, index_h + 1, index_v + 1, middle_x, middle_y, length_x, length_y, [], self.status)
                    sub_cells = [cells_l_b, cells_r_b, cells_l_t, cells_r_t]


        return  sub_cells




def extract_connecting_boders_between_points( cell_min_point, cell_length_x, cell_length_y, point_begin, point_end, result_type = "segments"):
    """
    There is an rectangle and two points on the border, this function is used to extract the borders connecting
    these two points. The segments must be clockwise
    Parameters
    ----------
    cell_min_point      : list
                          the bottom-left point of the cell, like [x0, y0]
    cell_length_x       : float
                          width of the cell
    cell_length_y       : float
                          height of the cell
    point_begin         : list
                          the first point on the cell's border. like [xa, ya]
    point_end           : list
                          the second point on the cell's border. like [xb, yb]
    result_type         : str
                          MUST be one of ["segments", "border_ids"]. Indicts which kind of result will return.
                          "segments": return the segments list which connecting these two points
                          "border_ids" return a list of ids of the orders of the cell connceting these two points

    Returns
    -------
    segments            : array
                          list of points
    ids                 : array
                          list of integers
    """
    if point_begin==point_end:
        return []
    # Determine which borders do the point_begin and point_end belong
    border_id_p_begin = -1
    border_id_p_end = -1
    if point_begin[0] == cell_min_point[0]:
        border_id_p_begin = 0
    elif point_begin[1] == cell_min_point[1]+cell_length_y:
        border_id_p_begin = 1
    elif point_begin[0] == cell_min_point[0]+cell_length_x:
        border_id_p_begin = 2
    elif point_begin[1] == cell_min_point[1]:
        border_id_p_begin = 3

    if point_end[0] == cell_min_point[0]:
        border_id_p_end = 0
    elif point_end[1] == cell_min_point[1]+cell_length_y:
        border_id_p_end = 1
    elif point_end[0] == cell_min_point[0]+cell_length_x:
        border_id_p_end = 2
    elif point_end[1] == cell_min_point[1]:
        border_id_p_end = 3

    if border_id_p_begin == -1 or border_id_p_end == -1:
        raise Exception("Error! begin/end point doesn't lie on the cell border!!!")


    # Now, move forward from point_begin to point_end
    segments = [point_begin]
    involved_border_ids = [border_id_p_begin]
    border_id_p_search = border_id_p_begin
    if border_id_p_search == border_id_p_end:  #first check if they lie on the same border at the beginning
        if border_id_p_search == 0:
            if point_begin[1] < point_end[1]:
                segments.append(point_end)
                if result_type == "segments":
                    return  segments
                else:
                    return involved_border_ids
            else:
                segments.append([cell_min_point[0], cell_min_point[1]+cell_length_y])
                border_id_p_search = (border_id_p_search + 1) %4
        if border_id_p_search == 1:
            if point_begin[0] < point_end[0]:
                segments.append(point_end)
                if result_type == "segments":
                    return  segments
                else:
                    return involved_border_ids
            else:
                segments.append([cell_min_point[0]+cell_length_x, cell_min_point[1]+cell_length_y])
                border_id_p_search = (border_id_p_search + 1) % 4
        if border_id_p_search == 2:
            if point_begin[1] > point_end[1]:
                segments.append(point_end)
                if result_type == "segments":
                    return segments
                else:
                    return involved_border_ids
            else:
                segments.append([cell_min_point[0]+cell_length_x, cell_min_point[1]])
                border_id_p_search = (border_id_p_search + 1) % 4
        if border_id_p_search == 1:
            if point_begin[0] > point_end[0]:
                segments.append(point_end)
                if result_type == "segments":
                    return segments
                else:
                    return involved_border_ids
            else:
                segments.append([cell_min_point[0] + cell_length_x, cell_min_point[1]])
                border_id_p_search = (border_id_p_search + 1) % 4
    while True:
        involved_border_ids.append(border_id_p_search)
        if border_id_p_search != border_id_p_end:  # add a whole border
            if border_id_p_search == 0:
                segments.append([cell_min_point[0], cell_min_point[1]+cell_length_y])
            elif border_id_p_search == 1:
                segments.append([cell_min_point[0]+cell_length_x, cell_min_point[1]+cell_length_y])
            elif border_id_p_search == 2:
                segments.append([cell_min_point[0]+cell_length_x, cell_min_point[1]])
            elif border_id_p_search == 3:
                segments.append([cell_min_point[0], cell_min_point[1]])
            border_id_p_search = (border_id_p_search + 1) % 4
        else:  # add the border segment according to the enc point
            segments.append(point_end)
            if result_type == "segments":
                return segments
            else:
                return involved_border_ids



def extract_segments_from_cell_with_arcs( cell_min_point, cell_length_x, cell_length_y, arcs, result_type="segments"):
    """
    At the end of study area quadtree dividing, there will be some node cells intersect with arcs. The arcs are segments
    of original study border and the begin and end points of the arcs MUST lie on node cell border. This function can
    intersect the node cell and
    Parameters
    ----------
    cell_min_point      : array
                          the bottom-left point of the cell, like [x0, y0]
    cell_length_x       : float
                          width of the cell
    cell_length_y       : float
                          height of the cell
    arcs                : array
                          array of point lists
    result_type         : str
                          MUST be one of ["segments", "border_ids"]. Indicts which kind of result will return.
                          "segments": return the segments list which connecting these two points
                          "border_ids" return a list of ids of the orders of the cell connceting these two points

    Returns
    -------

    """

def compare_distance_to_cell_left_bottom_point(cell_min_point, cell_length_x, cell_length_y, point_a, point_b):
    """
    When both two points lie on the borders of a cell (rectangle), This function is used to compare the distances of
    two points to the left_bottom
    Parameters
    ----------
    cell_min_point      : list
                          the bottom-left point of the cell, like [x0, y0]
    cell_length_x       : float
                          width of the cell
    cell_length_y       : float
                          height of the cell
    point_a             : list
                          the first point on the cell's border. like [xa, ya]
    point_b             : list
                          the second point on the cell's border. like [xb, yb]

    Returns
    -------
    compare_result      : int
                          if point_a = point_b, return 0;
                          if point_a is closer, return -1
                          if point_a is far, return 1
    """
    if point_a == point_b:
        return 0
    border_id_p_a = -1
    border_id_p_b = -1
    if point_a[0] == cell_min_point[0]:
        border_id_p_a = 0
    elif point_a[1] == cell_min_point[1] + cell_length_y:
        border_id_p_a = 1
    elif point_a[0] == cell_min_point[0] + cell_length_x:
        border_id_p_a = 2
    elif point_a[1] == cell_min_point[1]:
        border_id_p_a = 3

    if point_b[0] == cell_min_point[0]:
        border_id_p_b = 0
    elif point_b[1] == cell_min_point[1] + cell_length_y:
        border_id_p_b = 1
    elif point_b[0] == cell_min_point[0] + cell_length_x:
        border_id_p_b = 2
    elif point_b[1] == cell_min_point[1]:
        border_id_p_b = 3

    if border_id_p_a == -1 or border_id_p_b == -1:
        raise Exception("One or more Points not lie on the cell's border")
    if border_id_p_a != border_id_p_b:
        if border_id_p_a>border_id_p_b:
            return 1
        else:
            return -1
    else:
        if border_id_p_a == 0:
            if point_a[1] > point_b[1]:
                return 1;
            else:
                return -1
        if border_id_p_a == 1:
            if point_a[0] > point_b[0]:
                return 1;
            else:
                return -1
        if border_id_p_a == 2:
            if point_a[1] < point_b[1]:
                return 1;
            else:
                return -1
        if border_id_p_a == 3:
            if point_a[0] < point_b[0]:
                return 1;
            else:
                return -1

