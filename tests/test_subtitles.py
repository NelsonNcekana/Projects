import unittest

from autoreels.subtitles import build_srt


class TestSubtitles(unittest.TestCase):
    def test_build_srt_has_blocks_and_timestamps(self) -> None:
        text = build_srt(["Hook line", "Main point", "CTA"], total_duration=12.0)
        self.assertIn("00:00:00,000 --> 00:00:04,000", text)
        self.assertIn("Hook line", text)
        self.assertIn("CTA", text)


if __name__ == "__main__":
    unittest.main()
