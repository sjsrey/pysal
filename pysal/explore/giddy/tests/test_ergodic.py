import unittest
from .. import ergodic
import numpy as np


class SteadyState_Tester(unittest.TestCase):
    def setUp(self):
        self.p = np.array([[.5, .25, .25], [.5, 0, .5], [.25, .25, .5]])
        self.p2 = np.array([[.5, .5, 0], [.3, .7, 0], [0, 0, 1]])
        self.p3 = np.array([[.5, .5, 0], [.3, .7, 0], [0, 0, 0]])

    def test_steady_state_ergodic(self):
        obs = ergodic._steady_state_ergodic(self.p)
        exp = np.array([0.4, 0.2, 0.4])
        np.testing.assert_array_almost_equal(exp, obs)

    def test_steady_state(self):
        obs = ergodic.steady_state(self.p)
        exp = np.array([0.4, 0.2, 0.4])
        np.testing.assert_array_almost_equal(exp, obs)

        obs = ergodic.steady_state(self.p2)
        exp = np.array([[0.375, 0.625, 0.   ], [0.   , 0.   , 1.   ]])
        np.testing.assert_array_almost_equal(exp, obs)

        obs = ergodic.steady_state(self.p3, fill_empty_classes=True)
        exp = np.array([[0.375, 0.625, 0.], [0., 0., 1.]])
        np.testing.assert_array_almost_equal(exp, obs)

        self.assertRaises(ValueError, ergodic.steady_state, self.p3, False)



class Fmpt_Tester(unittest.TestCase):
    def setUp(self):
        self.p = np.array([[.5, .25, .25], [.5, 0, .5], [.25, .25, .5]])
        self.p2 = np.array([[.5, .5, 0], [.3, .7, 0], [0, 0, 1]])
        self.p3 = np.array([[.5, .5, 0], [.3, .7, 0], [0, 0, 0]])

    def test_fmpt_ergodic(self):
        obs = ergodic._fmpt_ergodic(self.p)
        exp = np.array([[2.5, 4., 3.33333333], [2.66666667, 5.,
                                                 2.66666667], [3.33333333, 4., 2.5]])
        np.testing.assert_array_almost_equal(exp, obs)

    def test_fmpt(self):
        obs = ergodic.fmpt(self.p)
        exp = np.array([[2.5, 4., 3.33333333], [2.66666667, 5.,
                                                 2.66666667], [3.33333333, 4., 2.5]])
        np.testing.assert_array_almost_equal(exp, obs)

        obs = ergodic.fmpt(self.p2)
        exp = np.array([[2.66666667, 2.        ,       np.inf],
                        [3.33333333, 1.6       ,       np.inf],
                        [    np.inf,     np.inf, 1.        ]])
        np.testing.assert_array_almost_equal(exp, obs)

        obs = ergodic.fmpt(self.p3, fill_empty_classes=True)
        exp = np.array([[2.66666667, 2., np.inf],
                        [3.33333333, 1.6, np.inf],
                        [np.inf, np.inf, 1.]])
        np.testing.assert_array_almost_equal(exp, obs)

class VarFmpt_Tester(unittest.TestCase):
    def setUp(self):
        self.p = np.array([[.5, .25, .25], [.5, 0, .5], [.25, .25, .5]])

    def test_var_fmpt(self):
        obs = ergodic.var_fmpt_ergodic(self.p)
        exp = np.array([[5.58333333, 12., 6.88888889], [6.22222222,
                                                         12., 6.22222222], [6.88888889, 12., 5.58333333]])
        np.testing.assert_array_almost_equal(exp, obs)


suite = unittest.TestSuite()
test_classes = [SteadyState_Tester, Fmpt_Tester, VarFmpt_Tester]
for i in test_classes:
    a = unittest.TestLoader().loadTestsFromTestCase(i)
    suite.addTest(a)

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite)
