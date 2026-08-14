import unittest

import numpy as np

import wildidea_w1 as w1


class WildIdeaW1Tests(unittest.TestCase):
    def test_scan_hits_all_four_defect_centers_at_probe_times(self):
        positions = [w1.deterministic_scan_position(t) for t in w1.PULSE_TIMES]
        self.assertEqual(tuple(positions), w1.DEFECT_CENTERS)

    def test_passive_and_controlled_share_initial_ambient_state_but_probe_diverges(self):
        passive = w1.simulate_episode(0, 12345, "passive")
        controlled = w1.simulate_episode(0, 12345, "controlled")
        self.assertEqual(passive.pulse_count, 0)
        self.assertEqual(controlled.pulse_count, 4)
        self.assertFalse(np.allclose(passive.field, controlled.field))

    def test_controlled_write_budget_is_label_independent(self):
        for class_id in range(4):
            episode = w1.simulate_episode(class_id, 777 + class_id, "controlled")
            self.assertEqual(episode.pulse_count, 4)
            self.assertEqual(episode.pulse_amplitude, w1.PULSE_AMPLITUDE)

    def test_feature_width_is_equal(self):
        fmap = w1.FixedFeatureMap()
        passive = w1.simulate_episode(1, 909, "passive")
        controlled = w1.simulate_episode(1, 909, "controlled")
        vectors = [
            fmap.static_global(passive),
            fmap.recurrent_global(passive),
            fmap.scout(passive),
            fmap.scout(controlled),
        ]
        self.assertTrue(all(v.shape == (w1.FEATURE_WIDTH,) for v in vectors))

    def test_small_smoke_run_returns_all_architectures(self):
        result = w1.run_benchmark(train_episodes=40, test_episodes=40)
        self.assertEqual(set(result["results"]), set(w1.ARCHITECTURES))
        self.assertIn(result["verdict"], {"ACTIVE_PROBING_EARNS_KEEP", "ACTIVE_PROBING_NOT_EARNED"})


if __name__ == "__main__":
    unittest.main()
