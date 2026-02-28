import unittest

from autoreels.models import CampaignConfig


class TestCampaignConfig(unittest.TestCase):
    def test_campaign_config_requires_topics(self) -> None:
        with self.assertRaises(ValueError):
            CampaignConfig.from_dict({"brand_name": "x", "topics": []})

    def test_campaign_config_parses_topics(self) -> None:
        cfg = CampaignConfig.from_dict(
            {
                "brand_name": "Brand",
                "niche": "niche",
                "default_cta": "Follow",
                "topics": [{"topic": "A topic"}],
            }
        )
        self.assertEqual(cfg.brand_name, "Brand")
        self.assertEqual(cfg.topics[0].topic, "A topic")


if __name__ == "__main__":
    unittest.main()
