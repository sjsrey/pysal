#import os
#import unittest
#import pysal
#import numpy as np
#from pysal.weights import user2 as newW
#ps=pysal

#class Testuser(unittest.TestCase):
#    def setUp(self):
#        self.columbus = pysal.examples.get_path("columbus.shp")
#        self.juvenile = pysal.examples.get_path('juvenile.shp')
#        self.wq = newW.W_Queen(pysal.open(self.columbus))
#        self.wr = newW.W_Rook(pysal.open(self.columbus))
#    def test_queen(self):
#        self.assertAlmostEquals(self.wq.pct_nonzero, 9.82923781757601)
#
#    def test_rook(self):
#        self.assertAlmostEquals(self.wr.pct_nonzero, 8.329862557267806)
#
#    def test_knnW_array(self):
#        x, y = np.indices((5, 5))
#        x.shape = (25, 1)
#        y.shape = (25, 1)
#        data = np.hstack([x, y])
#        wnn2 = newW.W_Knn(data, k=2)
#        wnn4 = newW.W_Knn(data, k=4)
#        self.assertEquals(set(wnn4.neighbors[0]), set([1, 5, 6, 2]))
#        self.assertEquals(set(wnn4.neighbors[5]), set([0, 6, 10, 1]))
#        self.assertEquals(set(wnn2.neighbors[0]), set([1, 5]))
#        self.assertEquals(set(wnn2.neighbors[5]), set([0, 6]))
#        self.assertAlmostEquals(wnn2.pct_nonzero, 8.0)
#        self.assertAlmostEquals(wnn4.pct_nonzero, 16.0)
#        wnn4 = newW.W_Knn(data, k=4)
#        self.assertEquals(set(wnn4.neighbors[0]), set([1, 5, 6, 2]))
#        '''
#        wnn3e = pysal.knnW(data, p=2, k=3)
#        self.assertEquals(set(wnn3e.neighbors[0]),set([1, 5, 6]))
#        wnn3m = pysal.knnW(data, p=1, k=3)
#        self.assertEquals(set(wnn3m.neighbors[0]), set([1, 5, 2]))
#        '''
#
#    def test_knnW_file(self):
#        wc = newW.W_Knn(ps.open(self.columbus))
#        self.assertAlmostEquals(wc.pct_nonzero, 4.081632653061225)
#        wc3 = newW.W_Knn(ps.open(self.columbus), k=3)
#        self.assertEquals(wc3.weights[1], [1, 1, 1])
#        self.assertEquals(set(wc3.neighbors[1]), set([3, 0, 7]))
#        self.assertEquals(set(wc.neighbors[0]), set([2, 1]))
#        w = newW.W_Knn(ps.open(self.juvenile))
#        self.assertAlmostEquals(w.pct_nonzero, 1.1904761904761904)
#        w1 = newW.W_Knn(ps.open(self.juvenile), k=1)
#        self.assertAlmostEquals(w1.pct_nonzero, 0.5952380952380952)
#
#    def test_threshold_binaryW_array(self):
#        points = [(10, 10), (20, 10), (40, 10), (15, 20), (30, 20), (30, 30)]
#        w = newW.W_Threshold_Binary(points, threshold=11.2)
#        self.assertEquals(w.weights, {0: [1, 1], 1: [1, 1], 2: [],
#                                      3: [1, 1], 4: [1], 5: [1]})
#        self.assertEquals(w.neighbors, {0: [1, 3], 1: [0, 3], 2: [
#        ], 3: [1, 0], 4: [5], 5: [4]})
#
#    def test_threshold_binaryW_file(self):
#        w = newW.W_Threshold_Binary(ps.open(self.columbus), 0.62)#, idVariable="POLYID")
#        self.assertEquals(w.weights[1], [1, 1])
#
#    def test_threshold_continuousW_array(self):
#        points = [(10, 10), (20, 10), (40, 10), (15, 20), (30, 20), (30, 30)]
#        wid = newW.W_Threshold_Continuous(points, 11.2)
#        self.assertEquals(wid.weights[0], [0.10000000000000001,
#                                           0.089442719099991588])
#        wid2 = newW.W_Threshold_Continuous(points, 11.2, alpha=-2.0)
#        self.assertEquals(wid2.weights[0], [0.01, 0.0079999999999999984])
#
#    def test_threshold_continuousW_file(self):
#        w = newW.W_Threshold_Continuous(ps.open(self.columbus), 0.62)#, idVariable="POLYID")
#        self.assertEquals(
#            w.weights[1], [1.6702346893743334, 1.7250729841938093])
#
#    def test_kernelW_array(self):
#        points = [(10, 10), (20, 10), (40, 10), (15, 20), (30, 20), (30, 30)]
#        kw = newW.W_Kernel(points)
#        self.assertEquals(kw.weights[0], [1.0, 0.50000004999999503,
#                                          0.44098306152674649])
#        self.assertEquals(kw.neighbors[0], [0, 1, 3])
#        np.testing.assert_array_almost_equal(
#            kw.bandwidth, np.array([[20.000002],
#                                    [20.000002],
#                                    [20.000002],
#                                    [20.000002],
#                                    [20.000002],
#                                    [20.000002]]))
#
#    def test_min_threshold_dist(self):
#        f = self.columbus
#        min_d = pysal.min_threshold_dist_from_shapefile(f)
#        self.assertAlmostEquals(min_d, 0.61886415807685413)
#
#    def test_kernelW_file(self):
#        kw = newW.W_Kernel(ps.open(self.columbus))#, idVariable='POLYID')
#        self.assertEquals(set(kw.weights[1]), set([0.0070787731484506233,
#                                         0.2052478782400463,
#                                         0.23051223027663237,
#                                         1.0
#                                         ]))
#        np.testing.assert_array_almost_equal(
#            kw.bandwidth[:3], np.array([[0.75333961], [0.75333961],
#                                        [0.75333961]]))
#
#    def test_adaptive_kernelW_array(self):
#        points = [(10, 10), (20, 10), (40, 10), (15, 20), (30, 20), (30, 30)]
#        bw = [25.0, 15.0, 25.0, 16.0, 14.5, 25.0]
#        kwa = pysal.adaptive_kernelW(points, bandwidths=bw)
#        self.assertEqual(kwa.weights[0], [1.0, 0.59999999999999998,
#                                          0.55278640450004202,
#                                          0.10557280900008403])
#        self.assertEqual(kwa.neighbors[0], [0, 1, 3, 4])
#        np.testing.assert_array_almost_equal(kwa.bandwidth,
#                                             np.array([[25.], [15.], [25.],
#                                                      [16.], [14.5], [25.]]))
#
#        kweag = pysal.adaptive_kernelW(points, function='gaussian')
#        self.assertEqual(
#            kweag.weights[0], [0.3989422804014327, 0.26741902915776961,
#                               0.24197074871621341])
#        np.testing.assert_array_almost_equal(kweag.bandwidth,
#                                             np.array([[11.18034101],
#                                                       [11.18034101],
#                                                       [20.000002],
#                                                       [11.18034101],
#                                                       [14.14213704],
#                                                       [18.02775818]]))
#
#    def test_adaptive_kernelW_file(self):
#        kwa = newW.W_Kernel_Adaptive(ps.open(self.columbus))
#        self.assertEquals(kwa.weights[0], [1.0, 0.03178906767736345,
#                                           9.9999990066379496e-08])
#        np.testing.assert_array_almost_equal(kwa.bandwidth[:3],
#                                             np.array([[0.59871832],
#                                                       [0.59871832],
#                                                       [0.56095647]]))
#
#    def test_build_lattice_shapefile(self):
#        of = "lattice.shp"
#        pysal.build_lattice_shapefile(20, 20, of)
#        w = newW.W_Rook(ps.open(of))
#        self.assertEquals(w.n, 400)
#        os.remove('lattice.shp')
#        os.remove('lattice.shx')
#

#suite = unittest.TestLoader().loadTestsFromTestCase(Testuser)

if __name__ == '__main__':
    pass
#    runner = unittest.TextTestRunner()
#    runner.run(suite)
