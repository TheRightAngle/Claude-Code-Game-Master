import json

from lib.campaign_manager import CampaignManager


def make_world_state(tmp_path):
    ws = tmp_path / "world-state"
    campaigns = ws / "campaigns"
    campaigns.mkdir(parents=True)

    hero = campaigns / "hero-campaign"
    hero.mkdir()
    (hero / "campaign-overview.json").write_text(
        json.dumps({"campaign_name": "Hero Campaign"}, ensure_ascii=False)
    )
    return ws


class TestCampaignPathTraversalProtection:
    def test_create_rejects_traversal_name(self, tmp_path):
        ws = make_world_state(tmp_path)
        mgr = CampaignManager(str(ws))

        outside = tmp_path / "escaped-campaign"
        result = mgr.create("../../escaped-campaign")

        assert result is None
        assert not outside.exists()

    def test_set_active_rejects_traversal_name(self, tmp_path):
        ws = make_world_state(tmp_path)
        mgr = CampaignManager(str(ws))
        assert mgr.set_active("hero-campaign") is True

        assert mgr.set_active("../../escaped-campaign") is False
        assert mgr.get_active() == "hero-campaign"

    def test_delete_rejects_traversal_name(self, tmp_path):
        ws = make_world_state(tmp_path)
        mgr = CampaignManager(str(ws))

        outside = tmp_path / "escaped-campaign"
        outside.mkdir()
        (outside / "keep.txt").write_text("do not delete")

        assert mgr.delete("../../escaped-campaign", confirm=True) is False
        assert outside.exists()
        assert (outside / "keep.txt").exists()

    def test_get_campaign_path_rejects_traversal_name(self, tmp_path):
        ws = make_world_state(tmp_path)
        mgr = CampaignManager(str(ws))

        assert mgr.get_campaign_path("../../escaped-campaign") is None

    def test_get_active_campaign_dir_rejects_tampered_active_file(self, tmp_path):
        ws = make_world_state(tmp_path)
        mgr = CampaignManager(str(ws))

        outside = tmp_path / "escaped-campaign"
        outside.mkdir()
        (ws / "active-campaign.txt").write_text("../../escaped-campaign")

        assert mgr.get_active_campaign_dir() is None
