import unittest

from autoreels.utils import slugify


class TestUtils(unittest.TestCase):
    def test_slugify_normalizes_text(self) -> None:
        self.assertEqual(slugify("  Hello, World!! "), "hello-world")


if __name__ == "__main__":
    unittest.main()
