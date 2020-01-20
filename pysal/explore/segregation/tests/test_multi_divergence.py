import unittest
import pytest
import pysal.lib
import geopandas as gpd
import numpy as np
from pysal.explore.segregation.aspatial import MultiDivergence


class Multi_Divergence_Tester(unittest.TestCase):
    @pytest.mark.slow
    def test_Multi_Divergence(self):
        s_map = gpd.read_file(pysal.lib.examples.get_path("sacramentot2.shp"))
        groups_list = ['WHITE_', 'BLACK_', 'ASIAN_','HISP_']
        df = s_map[groups_list]
        index = MultiDivergence(df, groups_list)
        np.testing.assert_almost_equal(index.statistic, 0.16645182134289443)


if __name__ == '__main__':
    unittest.main()
