import unittest

import numpy as np

import wildidea_w4_nuisance as w4
import wildidea_w4b_validated_fixed as w4b


class W4bValidatedFixedTests(unittest.TestCase):
    def test_ordered_schedule_count(self):
        schedules = w4b.ordered_schedules()
        self.assertEqual(len(schedules), 336)
        self.assertEqual(len(set(schedules)), 336)
        self.assertTrue(all(len(set(s)) == 3 for s in schedules))

    def test_projector_matches_direct_quotient_loss(self):
        rng = np.random.default_rng(123)
        means = rng.normal(size=(w4.N_CLASSES, w4.N_CLASSES, w4.RECEIPT_DIM))
        projectors = w4b.quotient_projectors(means)
        y = rng.normal(size=w4.RECEIPT_DIM)
        variance = 0.7
        for class_id in (0, 3, 7):
            for probe_index in (0, 4, 7):
                residual = projectors[class_id, probe_index] @ y
                projected_loss = float(np.mean(residual * residual) / variance)
                direct_loss = w4.quotient_class_loss(
                    y,
                    means[class_id, probe_index],
                    variance,
                )
                self.assertAlmostEqual(projected_loss, direct_loss, places=10)

    def test_fixed_schedule_evaluator_uses_round_order(self):
        ll = np.zeros((2, 3, w4.N_CLASSES, w4.N_CLASSES), dtype=float)
        truth = np.array([0, 1], dtype=int)
        ll[0, 0, 0, 0] = 5.0
        ll[0, 1, 1, 0] = 5.0
        ll[0, 2, 2, 0] = 5.0
        ll[1, 0, 0, 1] = 5.0
        ll[1, 1, 1, 1] = 5.0
        ll[1, 2, 2, 1] = 5.0
        acc, pred = w4b.evaluate_fixed_schedule(ll, truth, (0, 1, 2))
        self.assertEqual(acc, 1.0)
        np.testing.assert_array_equal(pred, truth)


if __name__ == "__main__":
    unittest.main()
