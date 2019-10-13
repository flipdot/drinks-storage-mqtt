#!/usr/bin/env python3
import unittest

from config import ScaleConfig


class ScaleConfigTest(unittest.TestCase):
    def test_toCrates(self):
        myScale = ScaleConfig(
            scale_name='apfelschorle',
            tare_raw=8149431,
            crate_raw=-261813,
            kilogram_raw=-23350,
            tolerance_kg=0.7,
        )

        # calc one crate
        self.assertAlmostEqual(myScale.to_crates(8149431), 0)

        # calc one crate
        self.assertAlmostEqual(myScale.to_crates(8149431 - 261813), 1)

        # calc two crate
        self.assertAlmostEqual(myScale.to_crates(8149431 - 2 * 261813), 2)

    def test_calcCrates(self):
        myScale = ScaleConfig(
            scale_name='apfelschorle',
            tare_raw=8149431,
            crate_raw=-261813,
            kilogram_raw=-23350,
            tolerance_kg=0.7,
        )

        # calc one crate
        self.assertEqual(myScale.calc_crates(8149431), 0)

        # 0.5kg off should be ok
        self.assertEqual(myScale.calc_crates(8149431 - (0.5 * 23350)), 0)

        # 1kg off should raise an error
        with self.assertRaises(ValueError):
            myScale.calc_crates(8149431 - 23350)


if __name__ == '__main__':
    unittest.main()
