# -*- coding: utf-8 -*-
"""estimate.py 的单元测试。

运行：
    python -m unittest discover -s tests -v
"""

import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import estimate  # noqa: E402


class TestBaseConversion(unittest.TestCase):
    def test_parse_int_binary(self):
        self.assertEqual(estimate.parse_int("10110101", 2), 181)
        self.assertEqual(estimate.parse_int("0b10110101", 10), 181)
        self.assertEqual(estimate.parse_int("1_011_0101", 2), 181)

    def test_parse_int_hex(self):
        self.assertEqual(estimate.parse_int("1A", 16), 26)
        self.assertEqual(estimate.parse_int("0xFF", 10), 255)
        self.assertEqual(estimate.parse_int("b5", 16), 181)

    def test_parse_int_rejects_bad_digit(self):
        with self.assertRaises(ValueError):
            estimate.parse_int("102", 2)
        with self.assertRaises(ValueError):
            estimate.parse_int("G", 16)

    def test_to_base(self):
        self.assertEqual(estimate.to_base(255, 16), "FF")
        self.assertEqual(estimate.to_base(181, 2), "10110101")
        self.assertEqual(estimate.to_base(26, 2), "11010")
        self.assertEqual(estimate.to_base(0, 2), "0")

    def test_weight_table_sum(self):
        total, text = estimate.weight_table("10110101", 2)
        self.assertEqual(total, 181)
        self.assertIn("2^7 = 128", text)

    def test_round_trip(self):
        for value in (0, 1, 7, 255, 256, 4095, 123456789):
            for base in (2, 8, 10, 16):
                self.assertEqual(estimate.parse_int(estimate.to_base(value, base), base), value)


class TestSizes(unittest.TestCase):
    def test_image(self):
        self.assertEqual(estimate.image_bytes(1920, 1080, 24), 6_220_800)

    def test_audio(self):
        self.assertEqual(estimate.audio_bytes(240, 44100, 16, 2), 42_336_000)
        self.assertEqual(estimate.audio_bytes(60, 44100, 16, 2), 10_584_000)

    def test_video(self):
        self.assertEqual(estimate.video_bytes(7200, 8), 7_200_000_000)

    def test_human_units(self):
        self.assertEqual(estimate.human_si(6_220_800), "6.2208 MB")
        self.assertEqual(estimate.human_iec(6_220_800), "5.9326 MiB")
        self.assertEqual(estimate.dual(7_200_000_000), "7.2 GB / 6.7055 GiB")


class TestFormatting(unittest.TestCase):
    def test_disp_width(self):
        self.assertEqual(estimate.disp_width("abc"), 3)
        self.assertEqual(estimate.disp_width("数制"), 4)
        self.assertEqual(estimate.disp_width("a数"), 3)

    def test_pad(self):
        self.assertEqual(estimate.pad("数", 4), "数  ")
        self.assertEqual(estimate.pad("1", 3, ">"), "  1")
        self.assertEqual(estimate.disp_width(estimate.pad("数", 5)), 5)


class TestCli(unittest.TestCase):
    def run_cli(self, *args):
        proc = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "estimate.py"), *args],
            capture_output=True, text=True, encoding="utf-8",
        )
        return proc

    def test_check_passes(self):
        proc = self.run_cli("check")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("全部通过", proc.stdout)
        self.assertNotIn("FAIL", proc.stdout)

    def test_convert_255(self):
        proc = self.run_cli("convert", "255", "--to", "16")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("FF", proc.stdout)

    def test_image_cli(self):
        proc = self.run_cli("image", "1920", "1080")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("6.2208 MB", proc.stdout)
        self.assertIn("5.9326 MiB", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
