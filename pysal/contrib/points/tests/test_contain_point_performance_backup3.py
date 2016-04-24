import pysal as ps
from pysal.cg.shapes import Polygon
import time
import codecs
import math

def compare_with_tolerance(a, b, tolerance = 0.000000001):
    """
    For the float value comparing, there are some situlation that two values are actually the same but been shown
    differently, e.g 1.230 and 1.2300000000000001. Especially after some calculation. This function is used to
    compare two float value with some tolerance
    Parameters
    ----------
    a           : float
                  the first value
    b           : float
                  the second value
    tolerance   : float
                  tolerance for the comparing

    Returns
    -------
    if_bigger_than  : int
                      if a is bigger than b
                      1: a > b
                      0: a == b
                      -1: a < b
    """
    tolerance = math.fabs(tolerance)
    if a - b > tolerance:
        return 1
    elif a - b < -tolerance:
        return  -1
    else:
        return 0

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
        self.zero_tolerance = 0.000000001

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
                # Do some initialize work, find one point lies on the border of the rectangle(cell) and begin with this point
                arc = self.arcs[0]
                if arc[0] == arc[len(arc)-1]:  # remove the duplicated points the the end of the arc
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
                        if compare_with_tolerance(x0, self.min_x, self.zero_tolerance) == 0:  # left border
                            if compare_with_tolerance(y0, middle_y, self.zero_tolerance) == -1:  # position 1
                                temp_arc_belonging = "l_b"
                            elif compare_with_tolerance(y0, middle_y, self.zero_tolerance) == 1:  # position 2
                                temp_arc_belonging = "l_t"
                            else:  # just by chance at the middle point
                                if compare_with_tolerance(y1, y0, self.zero_tolerance) == -1:  # going down
                                    temp_arc_belonging = "l_b"
                                elif compare_with_tolerance(y1, y0, self.zero_tolerance) == 1:  # going up
                                    temp_arc_belonging = "l_t"
                                else: # just by chance this segment lies on split_line_h, throw it
                                    continue
                        elif compare_with_tolerance(x0, self.min_x+self.length_x, self.zero_tolerance) == 0:  # right border
                            if compare_with_tolerance(y0, middle_y, self.zero_tolerance) == -1:  # position 6
                                temp_arc_belonging = "r_b"
                            elif compare_with_tolerance(y0, middle_y, self.zero_tolerance) == 1:  # position 5
                                temp_arc_belonging = "r_t"
                            else:  # just by chance at the middle point
                                if compare_with_tolerance(y1, y0, self.zero_tolerance) == -1:  # going down
                                    temp_arc_belonging = "r_b"
                                elif compare_with_tolerance(y1, y0, self.zero_tolerance) == 1:  # going up
                                    temp_arc_belonging = "r_t"
                                else:  # just by chance this segment lies on split_line_h, throw it
                                    continue
                        elif compare_with_tolerance(y0, self.min_y, self.zero_tolerance) == 0:  # bottom border
                            if compare_with_tolerance(x0, middle_x, self.zero_tolerance) == -1: # position 8
                                temp_arc_belonging = "l_b"
                            elif compare_with_tolerance(x0, middle_x, self.zero_tolerance) == 1: # position 7
                                temp_arc_belonging = "r_b"
                            else:  # just by chance at the middle point
                                if compare_with_tolerance(x1, x0, self.zero_tolerance) == -1:  # going left
                                    temp_arc_belonging = "l_b"
                                elif compare_with_tolerance(x1, x0, self.zero_tolerance) == 1:  #going right
                                    temp_arc_belonging = "r_b"
                                else:   # just by chance this segment lies on split_line_v, throw it
                                    continue
                        elif compare_with_tolerance(y0, self.min_y+self.length_y, self.zero_tolerance) == 0:  # top border
                            if compare_with_tolerance(x0, middle_x, self.zero_tolerance) == -1:  # position 3
                                temp_arc_belonging = "l_t"
                            elif compare_with_tolerance(x0, middle_x, self.zero_tolerance) == 1:  # position 4
                                temp_arc_belonging = "r_t"
                            else:  # just by chance at the middle point
                                if compare_with_tolerance(x1, x0, self.zero_tolerance) == -1:  # going left
                                    temp_arc_belonging = "l_t"
                                elif compare_with_tolerance(x1, x0, self.zero_tolerance) == 1:  # going right
                                    temp_arc_belonging = "r_t"
                                else:  # just by chance this segment lies on split_line_v, throw it
                                    continue
                        elif compare_with_tolerance(x0, middle_x, self.zero_tolerance) == 0:  # split_line_v
                            if compare_with_tolerance(y0, middle_y, self.zero_tolerance) == 1: # position c
                                if compare_with_tolerance(x1, x0, self.zero_tolerance) == 1:
                                    temp_arc_belonging = "r_t"
                                elif compare_with_tolerance(x1, x0, self.zero_tolerance) == -1:
                                    temp_arc_belonging = "l_t"
                                else:  # x1==x0, just by chance on the split_line_v
                                    continue
                            elif compare_with_tolerance(y0, middle_y, self.zero_tolerance) == -1: # position d
                                if compare_with_tolerance(x1, x0, self.zero_tolerance) == 1:
                                    temp_arc_belonging = "r_b"
                                elif compare_with_tolerance(x1, x0, self.zero_tolerance) == -1:
                                    temp_arc_belonging = "l_b"
                                else:  # x1==x0, just by chance on the split_line_v
                                    continue
                            else:  # in condition that p0 lies at the cross point of two split lines
                                if compare_with_tolerance(x1, x0, self.zero_tolerance) == 0 or compare_with_tolerance(y1, y0, self.zero_tolerance) == 0:  # on one of the split_line
                                    continue
                                elif compare_with_tolerance(x1, x0, self.zero_tolerance) == 1:
                                    if compare_with_tolerance(y1, y0, self.zero_tolerance) == 1:
                                        temp_arc_belonging = "r_t"
                                    else:
                                        temp_arc_belonging = "r_b"
                                else:  # on condition that x1 < x0
                                    if compare_with_tolerance(y1, y0, self.zero_tolerance) == 1:
                                        temp_arc_belonging = 'l_t'
                                    else:
                                        temp_arc_belonging = "l_b"
                        elif compare_with_tolerance(y0, middle_y, self.zero_tolerance) == 0:  # split_line_h
                            if compare_with_tolerance(x0, middle_x, self.zero_tolerance) == 1:  #position r
                                if compare_with_tolerance(y1, y0, self.zero_tolerance) == 1:
                                    temp_arc_belonging = "r_t"
                                elif compare_with_tolerance(y1, y0, self.zero_tolerance) == -1:
                                    temp_arc_belonging = "r_b"
                                else:  # y1==y0, just by chance on the split_line_h
                                    continue
                            else:  # on condition that x0 < middle_x, position a
                                if compare_with_tolerance(y1, y0, self.zero_tolerance) == 1:
                                    temp_arc_belonging = "l_t"
                                elif compare_with_tolerance(y1, y0, self.zero_tolerance) == -1:
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
                    if compare_with_tolerance(x0, x1, self.zero_tolerance) == compare_with_tolerance(x0, middle_x, self.zero_tolerance) == 0 or compare_with_tolerance(y0, y1, self.zero_tolerance) == compare_with_tolerance(y0, middle_y, self.zero_tolerance) == 0:  # split the arc here, throw current segment
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

                    intersect_point_h = None
                    intersect_point_v = None
                    # Check if the segment intersects with split_line_h
                    if (compare_with_tolerance(y0, middle_y, self.zero_tolerance) == -1 and compare_with_tolerance(middle_y, y1, self.zero_tolerance) <= 0) or ( compare_with_tolerance(y0, middle_y, self.zero_tolerance) == 1 and compare_with_tolerance(middle_y, y1, self.zero_tolerance) >= 0):
                        if compare_with_tolerance(x0, x1, self.zero_tolerance) == 0:  # the segments is vertical
                            intersect_point_h = [x0, middle_y]
                        else:
                            a = (y1 - y0) / (x1 - x0)
                            b = y0 - a * x0
                            x_new = (middle_y-b)/a
                            intersect_point_h = [x_new, middle_y]
                    # Check if the segment intersects with split_line_v
                    if (compare_with_tolerance(x0, middle_x, self.zero_tolerance) == -1 and compare_with_tolerance(middle_x, x1, self.zero_tolerance) <= 0) or (compare_with_tolerance(x0, middle_x, self.zero_tolerance) == 1 and compare_with_tolerance(middle_x, x1, self.zero_tolerance) >= 0):
                        if compare_with_tolerance(y0, y1, self.zero_tolerance) == 0:  # the segments is horizontal
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

                        if temp_arc_belonging == "l_b":
                            if intersect_point_mark == "h":
                                if (intersect_point_h is not None) and (intersect_point_v is not None):
                                    # under the situation that a single segment intersects with both split lines,
                                    # here need carefully process
                                    small_arc = [intersect_point_h, intersect_point_v]
                                    if compare_with_tolerance(intersect_point_h[0], intersect_point_v[0], self.zero_tolerance) != 0:  # deal with the situation that the segment just goes through center point
                                        cell_arcs_l_t.append(small_arc)
                                    temp_arc = [intersect_point_v, [x1, y1]]
                                    temp_arc_belonging = "r_t"
                                else:
                                    temp_arc = [intersect_point, [x1, y1]]
                                    temp_arc_belonging = "l_t"
                            else:
                                if (intersect_point_h is not None) and (intersect_point_v is not None):
                                    # under the situation that a single segment intersects with both split lines,
                                    # here need carefully process
                                    small_arc = [intersect_point_v, intersect_point_h]
                                    if compare_with_tolerance(intersect_point_h[0], intersect_point_v[0], self.zero_tolerance) != 0:  # deal with the situation that the segment just goes through center point
                                        cell_arcs_r_b.append(small_arc)
                                    temp_arc = [intersect_point_h, [x1, y1]]
                                    temp_arc_belonging = "r_t"
                                else:
                                    temp_arc = [intersect_point, [x1, y1]]
                                    temp_arc_belonging = "r_b"

                        elif temp_arc_belonging == "l_t":
                            if intersect_point_mark == "h":
                                if (intersect_point_h is not None) and (intersect_point_v is not None):
                                    # under the situation that a single segment intersects with both split lines,
                                    # here need carefully process
                                    small_arc = [intersect_point_h, intersect_point_v]
                                    if compare_with_tolerance(intersect_point_h[0], intersect_point_v[0], self.zero_tolerance) != 0:  # deal with the situation that the segment just goes through center point
                                        cell_arcs_l_b.append(small_arc)
                                    temp_arc = [intersect_point_v, [x1, y1]]
                                    temp_arc_belonging = "r_b"
                                else:
                                    temp_arc = [intersect_point, [x1, y1]]
                                    temp_arc_belonging = "l_b"
                            else:
                                if (intersect_point_h is not None) and (intersect_point_v is not None):
                                    # under the situation that a single segment intersects with both split lines,
                                    # here need carefully process
                                    small_arc = [intersect_point_v, intersect_point_h]
                                    if compare_with_tolerance(intersect_point_h[0], intersect_point_v[0], self.zero_tolerance) != 0:  # deal with the situation that the segment just goes through center point
                                        cell_arcs_r_t.append(small_arc)
                                    temp_arc = [intersect_point_h, [x1, y1]]
                                    temp_arc_belonging = "r_b"
                                else:
                                    temp_arc = [intersect_point, [x1, y1]]
                                    temp_arc_belonging = "r_t"

                        elif temp_arc_belonging == "r_b":
                            if intersect_point_mark == "h":
                                if (intersect_point_h is not None) and (intersect_point_v is not None):
                                    # under the situation that a single segment intersects with both split lines,
                                    # here need carefully process
                                    small_arc = [intersect_point_h, intersect_point_v]
                                    if compare_with_tolerance(intersect_point_h[0], intersect_point_v[0], self.zero_tolerance) != 0:  # deal with the situation that the segment just goes through center point
                                        cell_arcs_r_t.append(small_arc)
                                    temp_arc = [intersect_point_v, [x1, y1]]
                                    temp_arc_belonging = "l_t"
                                else:
                                    temp_arc = [intersect_point, [x1, y1]]
                                    temp_arc_belonging = "r_t"
                            else:
                                if (intersect_point_h is not None) and (intersect_point_v is not None):
                                    # under the situation that a single segment intersects with both split lines,
                                    # here need carefully process
                                    small_arc = [intersect_point_v, intersect_point_h]
                                    if compare_with_tolerance(intersect_point_h[0], intersect_point_v[0], self.zero_tolerance) != 0:  # deal with the situation that the segment just goes through center point
                                        cell_arcs_l_b.append(small_arc)
                                    temp_arc = [intersect_point_h, [x1, y1]]
                                    temp_arc_belonging = "l_t"
                                else:
                                    temp_arc = [intersect_point, [x1, y1]]
                                    temp_arc_belonging = "l_b"

                        elif temp_arc_belonging == "r_t":
                            if intersect_point_mark == "h":
                                if (intersect_point_h is not None) and (intersect_point_v is not None):
                                    # under the situation that a single segment intersects with both split lines,
                                    # here need carefully process
                                    small_arc = [intersect_point_h, intersect_point_v]
                                    if compare_with_tolerance(intersect_point_h[0], intersect_point_v[0], self.zero_tolerance) != 0:  # deal with the situation that the segment just goes through center point
                                        cell_arcs_r_b.append(small_arc)
                                    temp_arc = [intersect_point_v, [x1, y1]]
                                    temp_arc_belonging = "l_b"
                                else:
                                    temp_arc = [intersect_point, [x1, y1]]
                                    temp_arc_belonging = "r_b"
                            else:
                                if (intersect_point_h is not None) and (intersect_point_v is not None):
                                    # under the situation that a single segment intersects with both split lines,
                                    # here need carefully process
                                    small_arc = [intersect_point_v, intersect_point_h]
                                    if compare_with_tolerance(intersect_point_h[0], intersect_point_v[0], self.zero_tolerance) != 0:  # deal with the situation that the segment just goes through center point
                                        cell_arcs_l_t.append(small_arc)
                                    temp_arc = [intersect_point_h, [x1, y1]]
                                    temp_arc_belonging = "l_b"
                                else:
                                    temp_arc = [intersect_point, [x1, y1]]
                                    temp_arc_belonging = "l_t"
                        if compare_with_tolerance(temp_arc[0][0], temp_arc[1][0], self.zero_tolerance) == 0 and compare_with_tolerance(temp_arc[0][1], temp_arc[1][1], self.zero_tolerance) == 0:
                            # to deal with the situation that p1 just lied on one of the split-lines
                            temp_arc = []
                            temp_arc_belonging = None
                    else:  # simply append the point to current arc
                        if len(temp_arc) == 0:
                            temp_arc.append([x0, y0])
                        temp_arc.append([x1, y1])
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
            status_l_b = "maybe"
            status_l_t = "maybe"
            status_r_b = "maybe"
            status_r_t = "maybe"
            """
            At this point, all the arcs in this cell have been split into sub-arcs and allocated to 4 sub-cells.
            So, we can try to create the cells on left-bottom, right-bottom, left-top and right-top.
            Before doing that, we need to determine the status of each sub-cell, especially those who are totally
            within or out of the study area.
            These two kind of sub-cell have the same property: they don't have arc allocated. So, If here exists
            cell(s) who don't have arcs allocated, we need to begin the check
            """
            if len(cell_arcs_l_b)*len(cell_arcs_l_t)*len(cell_arcs_r_b)*len(cell_arcs_r_t) == 0:
                involved_line_ids = []  # refer the image in "cell_boundary_category_rule"

                # extract the involved borders of sub cells
                if len(cell_arcs_l_b) > 0:
                    extract_result = extract_segments_from_cell_with_arcs([self.min_x, self.min_y], length_x, length_y, cell_arcs_l_b, self.zero_tolerance)
                    line_ids = extract_result[1]
                    if 0 in line_ids:
                        involved_line_ids.append("1")
                    if 1 in line_ids:
                        involved_line_ids.append("a")
                    if 2 in line_ids:
                        involved_line_ids.append("d")
                    if 3 in line_ids:
                        involved_line_ids.append("8")
                if len(cell_arcs_l_t) > 0:
                    extract_result = extract_segments_from_cell_with_arcs([self.min_x, middle_y], length_x, length_y, cell_arcs_l_t, self.zero_tolerance)
                    line_ids = extract_result[1]
                    if 0 in line_ids:
                        involved_line_ids.append("2")
                    if 1 in line_ids:
                        involved_line_ids.append("3")
                    if 2 in line_ids:
                        involved_line_ids.append("c")
                    if 3 in line_ids:
                        involved_line_ids.append("a")
                if len(cell_arcs_r_b) > 0:
                    extract_result = extract_segments_from_cell_with_arcs([middle_x, self.min_y], length_x, length_y, cell_arcs_r_b, self.zero_tolerance)
                    line_ids = extract_result[1]
                    if 0 in line_ids:
                        involved_line_ids.append("d")
                    if 1 in line_ids:
                        involved_line_ids.append("b")
                    if 2 in line_ids:
                        involved_line_ids.append("6")
                    if 3 in line_ids:
                        involved_line_ids.append("7")
                if len(cell_arcs_r_t) > 0:
                    extract_result = extract_segments_from_cell_with_arcs([middle_x, middle_y], length_x, length_y, cell_arcs_r_t, self.zero_tolerance)
                    line_ids = extract_result[1]
                    if 0 in line_ids:
                        involved_line_ids.append("c")
                    if 1 in line_ids:
                        involved_line_ids.append("4")
                    if 2 in line_ids:
                        involved_line_ids.append("5")
                    if 3 in line_ids:
                        involved_line_ids.append("b")
                # determine the totally within and out-of sub cells
                if len(cell_arcs_l_b) == 0:
                    if "1" in involved_line_ids or "a" in involved_line_ids or "d" in involved_line_ids or "8" in involved_line_ids:
                        status_l_b = "in"
                    else:
                        status_l_b = "out"
                if len(cell_arcs_l_t) == 0:
                    if "2" in involved_line_ids or "3" in involved_line_ids or "c" in involved_line_ids or "a" in involved_line_ids:
                        status_l_t = "in"
                    else:
                        status_l_t = "out"
                if len(cell_arcs_r_b) == 0:
                    if "d" in involved_line_ids or "b" in involved_line_ids or "6" in involved_line_ids or "7" in involved_line_ids:
                        status_r_b = "in"
                    else:
                        status_r_b = "out"
                if len(cell_arcs_r_t) == 0:
                    if "c" in involved_line_ids or "4" in involved_line_ids or "5" in involved_line_ids or "b" in involved_line_ids:
                        status_r_t = "in"
                    else:
                        status_r_t = "out"

            cells_l_b = Cell(level, index_h, index_v, self.min_x, self.min_y, length_x, length_y, cell_arcs_l_b, status_l_b)
            cells_l_t = Cell(level, index_h, index_v + 1, self.min_x, middle_y, length_x, length_y, cell_arcs_l_t, status_l_t)
            cells_r_b = Cell(level, index_h + 1, index_v, middle_x, self.min_y, length_x, length_y, cell_arcs_r_b, status_r_b)
            cells_r_t = Cell(level, index_h + 1, index_v + 1, middle_x, middle_y, length_x, length_y, cell_arcs_r_t, status_r_t)
            sub_cells = [cells_l_b, cells_l_t, cells_r_b, cells_r_t]

        return sub_cells




def extract_connecting_borders_between_points(cell_min_point, cell_length_x, cell_length_y, point_begin, point_end, zero_tolerance):

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
    zero_tolerance      : float
                          value of zero_tolerance for determining if two float values are equal

    Returns
    -------
    segments_and_ids    : tuple
                          like (segments, involved_border_ids)
                          1. list of points, including the start and end points
                          2. list of border ids being involved in the segments, not necessary to be in the original order
    """
    if point_begin == point_end:
        return ([], [])
    # Determine which borders do the point_begin and point_end belong
    border_id_p_begin = -1
    border_id_p_end = -1
    if compare_with_tolerance(point_begin[0], cell_min_point[0], zero_tolerance) == 0:
        border_id_p_begin = 0
    elif compare_with_tolerance(point_begin[1], cell_min_point[1]+cell_length_y, zero_tolerance) == 0:
        border_id_p_begin = 1
    elif compare_with_tolerance(point_begin[0], cell_min_point[0]+cell_length_x, zero_tolerance) == 0:
        border_id_p_begin = 2
    elif compare_with_tolerance(point_begin[1], cell_min_point[1], zero_tolerance) == 0:
        border_id_p_begin = 3

    if compare_with_tolerance(point_end[0], cell_min_point[0], zero_tolerance) == 0:
        border_id_p_end = 0
    elif compare_with_tolerance(point_end[1], cell_min_point[1]+cell_length_y, zero_tolerance) == 0:
        border_id_p_end = 1
    elif compare_with_tolerance(point_end[0], cell_min_point[0]+cell_length_x, zero_tolerance) == 0:
        border_id_p_end = 2
    elif compare_with_tolerance(point_end[1], cell_min_point[1], zero_tolerance) == 0:
        border_id_p_end = 3

    if border_id_p_begin == -1 or border_id_p_end == -1:
        print(cell_min_point, cell_min_point[0]+cell_length_x, cell_min_point[1]+cell_length_y, point_begin, point_end, cell_length_x, cell_length_y)
        raise Exception("Error! begin/end point doesn't lie on the cell border!!!")


    # Now, move forward from point_begin to point_end
    segments = [point_begin]
    involved_border_ids = [border_id_p_begin]
    border_id_p_search = border_id_p_begin
    if border_id_p_search == border_id_p_end:  #first check if they lie on the same border at the beginning
        if border_id_p_search == 0:
            if compare_with_tolerance(point_begin[1], point_end[1], zero_tolerance) == -1:
                segments.append(point_end)
                return (segments, involved_border_ids)
            else:
                segments.append([cell_min_point[0], cell_min_point[1]+cell_length_y])
                border_id_p_search = (border_id_p_search + 1) %4
        if border_id_p_search == 1:
            if compare_with_tolerance(point_begin[0], point_end[0], zero_tolerance) == -1:
                segments.append(point_end)
                return (segments, involved_border_ids)
            else:
                segments.append([cell_min_point[0]+cell_length_x, cell_min_point[1]+cell_length_y])
                border_id_p_search = (border_id_p_search + 1) % 4
        if border_id_p_search == 2:
            if compare_with_tolerance(point_begin[1], point_end[1], zero_tolerance) == 1:
                segments.append(point_end)
                return (segments, involved_border_ids)
            else:
                segments.append([cell_min_point[0]+cell_length_x, cell_min_point[1]])
                border_id_p_search = (border_id_p_search + 1) % 4
        if border_id_p_search == 1:
            if compare_with_tolerance(point_begin[0], point_end[0], zero_tolerance) == 1:
                segments.append(point_end)
                return (segments, involved_border_ids)
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
            return (segments, list(set(involved_border_ids)))

def get_relative_location_on_cell_border(cell_min_point, cell_length_x, cell_length_y, point, zero_tolerance):
    """
    When a point is on the border of a cell, this function can be used to calculate the relative location of the point
    to cell's left-bottom corner.
    Parameters
    ----------
    cell_min_point      : list
                          the bottom-left point of the cell, like [x0, y0]
    cell_length_x       : float
                          width of the cell
    cell_length_y       : float
                          height of the cell
    point               : list
                          the point on the cell's border. like [x, y]
    zero_tolerance      : float
                          value of zero_tolerance for determining if two float values are equal

    Returns
    -------
    distance            : float
                          range from 0 to 4
    """
    border_id_p = -1
    if compare_with_tolerance(point[0], cell_min_point[0], zero_tolerance) == 0:
        border_id_p = 0
        border_id_p += (point[1]-cell_min_point[1]) / cell_length_y
    elif compare_with_tolerance(point[1], cell_min_point[1] + cell_length_y, zero_tolerance) == 0:
        border_id_p = 1
        border_id_p += (point[0]-cell_min_point[0]) / cell_length_x
    elif compare_with_tolerance(point[0], cell_min_point[0] + cell_length_x, zero_tolerance) == 0:
        border_id_p = 2
        border_id_p += (1 - (point[1]-cell_min_point[1]) / cell_length_y)
    elif compare_with_tolerance(point[1], cell_min_point[1], zero_tolerance) == 0:
        border_id_p = 3
        border_id_p += (1- (point[0]-cell_min_point[0]) / cell_length_x)
    return  border_id_p

def extract_segments_from_cell_with_arcs(cell_min_point, cell_length_x, cell_length_y, arcs, zero_tolerance):
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
    zero_tolerance      : float
                          value of zero_tolerance for determining if two float values are equal

    Returns
    -------
    rings_and_border_ids : tuple
                           like (rings, involved_border_ids)
                           1. the list of rings extracted, each ring contains a sequence of points -  the begin and end
                              points are the same. Note that there might be multiple rings extracted in a cell.
                           2. the ids of borders of the cell who are involved in the ring. Duplicated ids are removed
                              and they may not be in the original order
    """
    arc_begin_points = []  # beginning points of each arc
    arc_begin_points_location = []  # location of beginning points of each arc
    arc_end_points = []  # ending points of each arc
    arc_end_points_location = []# location of ending points of each arc
    for single_arc in arcs:
        arc_begin_points.append(single_arc[0])
        arc_end_points.append(single_arc[len(single_arc)-1])
        arc_begin_points_location.append(
            get_relative_location_on_cell_border(cell_min_point, cell_length_x, cell_length_y, single_arc[0], zero_tolerance))
        arc_end_points_location.append(
            get_relative_location_on_cell_border(cell_min_point, cell_length_x, cell_length_y, single_arc[len(single_arc)-1], zero_tolerance))

    rings = []
    involved_border_ids = []
    used_arc_ids = []
    # every time find an unused arc with minimum begin-point-location, and begin the track form here
    new_ring = []  # the point list
    new_ring_end_point = None
    new_ring_end_point_location = -1
    selected_arc_ids = []
    while len(used_arc_ids)<len(arcs):
        if len(selected_arc_ids) == 0:
            # init the process of constructing a new ring
            # find the unused arc with min begin point location
            arc_id_with_min_begin_location = -1
            for i in range(0, len(arcs)):
                if i in used_arc_ids:
                    continue
                if arc_id_with_min_begin_location == -1 or compare_with_tolerance(arc_begin_points_location[arc_id_with_min_begin_location], arc_begin_points_location[i], zero_tolerance) == 1:
                    arc_id_with_min_begin_location = i
            new_ring_end_point = arc_end_points[arc_id_with_min_begin_location]
            new_ring_end_point_location = arc_end_points_location[arc_id_with_min_begin_location]
            selected_arc_ids.append(arc_id_with_min_begin_location)
            for point in arcs[arc_id_with_min_begin_location]:
                new_ring.append(point)
        else:
            # there is already a selected arc, find the next available arc(maybe itself) and add the borders between
            # these two arcs
            arc_id_with_relatively_min_begin_location = -1
            for i in range(0, len(arcs)):
                if i in used_arc_ids:
                    continue
                if arc_id_with_relatively_min_begin_location == -1:
                    arc_id_with_relatively_min_begin_location = i
                else:
                    distance_to_end_point_min = arc_begin_points_location[arc_id_with_relatively_min_begin_location] - new_ring_end_point_location
                    if distance_to_end_point_min < 0:
                        distance_to_end_point_min += 4
                    distance_to_end_point_now = arc_begin_points_location[i] - new_ring_end_point_location
                    if distance_to_end_point_now < 0:
                        distance_to_end_point_now += 4
                    if compare_with_tolerance(distance_to_end_point_min, distance_to_end_point_now, zero_tolerance) == 1:
                        arc_id_with_relatively_min_begin_location = i
            extract_result = extract_connecting_borders_between_points(cell_min_point, cell_length_x, cell_length_y, new_ring_end_point, arc_begin_points[arc_id_with_relatively_min_begin_location], zero_tolerance)
            point_list = extract_result[0]
            border_id_list = extract_result[1]
            for i in range(0, len(point_list)):
                if i == 0 and point_list[i] == new_ring[len(new_ring)-1]:
                    continue
                new_ring.append(point_list[i])
            for border_id in border_id_list:
                if border_id not in  involved_border_ids:
                    involved_border_ids.append(border_id)
            new_ring_end_point = arc_end_points[arc_id_with_relatively_min_begin_location]
            new_ring_end_point_location = arc_end_points_location[arc_id_with_relatively_min_begin_location]
            if arc_id_with_relatively_min_begin_location not in selected_arc_ids:
                #  find a new arc, add the point sequence in this arc to the ring, and continue the searching further
                selected_arc_ids.append(arc_id_with_relatively_min_begin_location)
                single_arc = arcs[arc_id_with_relatively_min_begin_location]
                for i in range(0, len(single_arc)):
                    if i == 0 and single_arc[i] == new_ring[len(new_ring)-1]:
                        continue
                    new_ring.append(single_arc[i])
            else:
                # the newly found arc is exactly the beginning one, a whole closed ring is formed. stop here
                rings.append(new_ring)
                new_ring = []
                new_ring_end_point = None
                new_ring_end_point_location = -1
                for arc_id in selected_arc_ids:
                    used_arc_ids.append(arc_id)
                selected_arc_ids = []
    if len(new_ring)>0:
        raise Exception("Error in extract_segments_from_cell_with_arcs!!!")
    return (rings, involved_border_ids)






time_begin = int(round(time.time() * 1000))

pols = ps.open("data/Huangshan_region.shp")  # read the research region shape file
research_region = pols[0]  # set the first polygon as research polygon
print(len(research_region.vertices))  # pring the points count of research region polygon


# poi_file = codecs.open("data/poi_info_huangshan.txt", "r", encoding="UTF-8")
# print(poi_file.readline())
# line_stampe = 0
# count_points_in = 0
# count_points_out = 0
# for line in poi_file:
#     line_stampe += 1
#     if(len(line)<5):
#         continue
#     fields = line.split("\t")
#     if(len(fields)!=6):
#         continue
#     x = float(line.split("\t")[4])
#     y = float(line.split("\t")[5])
#     if research_region.contains_point((x, y)):
#         count_points_in += 1
#     else:
#         count_points_out += 1
#
# time_end = int(round(time.time() * 1000))
#
# print("finished")
# print(count_points_in, count_points_out)
# print(time_begin, time_end, time_end - time_begin)
vertices = research_region.vertices
vertices = [[0.0, 0.0], [3.0, 2.0], [5.0, 1.0]]

min_x = 0;
min_y = 0;
max_x = 0;
max_y = 0;
for i in range(0, len(vertices)):
    x = vertices[i][0]
    y = vertices[i][1]
    if i == 0:
        min_x = x
        min_y = y
        max_x = x
        max_y = y
    if min_x > x:
        min_x = x
    if max_x < x:
        max_x = x
    if min_y > y:
        min_y = y
    if max_y < y:
        max_y = y
top_cell = Cell(0, 0, 0, min_x, min_y, max_x-min_x, max_y-min_y, [vertices], "maybe")
result_cell_list = [top_cell]

for i in range(0, 7):
    temp_cell_list = []
    while len(result_cell_list) > 0:
        cell = result_cell_list.pop()
        sub_cell_list = cell.split()
        for sub_cell in sub_cell_list:
            temp_cell_list.append(sub_cell)
    result_cell_list = temp_cell_list

print(len(result_cell_list))
for cell in result_cell_list:
    middle_x = cell.min_x+cell.length_x/2
    middle_y = cell.min_y+cell.length_y/2
    print(",".join(map(str, [middle_x, middle_y, cell.status])))
# print("finish============")


