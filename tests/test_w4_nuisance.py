import unittest

import numpy as np

import wildidea_w4_nuisance as w4


class W4NuisanceTests(unittest.TestCase):
    def test_nuisance_only_pair_distance_is_zero(self):
        rng = np.random.default_rng(1)
        mu = rng.normal(size=w4.RECEIPT_DIM)
        other = 1.3 * mu + 0.07 * w4.ONES - 0.04 * w4.RAMP
        self.assertLess(w4.pair_distance_quotient(mu, other, 1.0), 1e-10)

    def test_structural_component_survives_quotient(self):
        rng = np.random.default_rng(2)
        mu = rng.normal(size=w4.RECEIPT_DIM)
        raw = np.sin(np.linspace(0.0, 9.0 * np.pi, w4.RECEIPT_DIM))
        structural = w4._least_squares_residual(raw, (mu, w4.ONES, w4.RAMP))
        self.assertGreater(
            w4.pair_distance_quotient(mu, mu + 0.2 * structural, 1.0),
            1e-5,
        )

    def test_quotient_class_loss_fits_declared_nuisance(self):
        rng = np.random.default_rng(3)
        mu = rng.normal(size=w4.RECEIPT_DIM)
        y = 0.8 * mu - 0.11 * w4.ONES + 0.03 * w4.RAMP
        self.assertLess(w4.quotient_class_loss(y, mu, 1.0), 1e-12)

    def test_pair_distance_is_symmetric(self):
        rng = np.random.default_rng(4)
        a = rng.normal(size=w4.RECEIPT_DIM)
        b = rng.normal(size=w4.RECEIPT_DIM)
        self.assertAlmostEqual(
            w4.pair_distance_quotient(a, b, 1.0),
            w4.pair_distance_quotient(b, a, 1.0),
            places=12,
        )


if __name__ == "__main__":
    unittest.main()
