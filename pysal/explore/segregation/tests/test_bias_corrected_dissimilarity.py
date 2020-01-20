import unittest
import pytest
import pysal.lib
import geopandas as gpd
import numpy as np
from pysal.explore.segregation.aspatial import BiasCorrectedDissim


class Bias_Corrected_Dissim_Tester(unittest.TestCase):
    @pytest.mark.slow
    def test_Bias_Corrected_Dissim(self):
        s_map = gpd.read_file(pysal.lib.examples.get_path("sacramentot2.shp"))
        df = s_map[['geometry', 'HISP_', 'TOT_POP']]
        np.random.seed(1234)
        index = BiasCorrectedDissim(df, 'HISP_', 'TOT_POP')
        np.testing.assert_almost_equal(index.statistic, 0.32136474449360836)


if __name__ == '__main__':
    unittest.main()
