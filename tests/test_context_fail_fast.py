import json

import pytest

import lib.world as world_module
from lib.campaign_manager import CampaignManager
from lib.entity_enhancer import EntityEnhancer
from lib.search import WorldSearcher
from lib.world_stats import WorldStats


def make_world_state(tmp_path, with_active=False):
    ws = tmp_path / "world-state"
    camp = ws / "campaigns" / "existing-campaign"
    camp.mkdir(parents=True)
    (camp / "campaign-overview.json").write_text(
        json.dumps({"campaign_name": "Existing"}, ensure_ascii=False)
    )
    if with_active:
        (ws / "active-campaign.txt").write_text("existing-campaign")
    return ws


class TestFailFastWithoutActiveCampaign:
    def test_searcher_raises_without_active_campaign(self, tmp_path):
        ws = make_world_state(tmp_path, with_active=False)
        with pytest.raises(RuntimeError):
            WorldSearcher(str(ws))

    def test_world_stats_raises_without_active_campaign(self, tmp_path):
        ws = make_world_state(tmp_path, with_active=False)
        with pytest.raises(RuntimeError):
            WorldStats(str(ws))

    def test_entity_enhancer_raises_without_active_campaign(self, tmp_path):
        ws = make_world_state(tmp_path, with_active=False)
        with pytest.raises(RuntimeError):
            EntityEnhancer(str(ws))


class TestWorldSetActiveFailure:
    def test_world_raises_when_set_active_fails(self, tmp_path, monkeypatch):
        ws = make_world_state(tmp_path, with_active=True)

        monkeypatch.setattr(
            world_module,
            "CampaignManager",
            lambda: CampaignManager(str(ws)),
        )

        with pytest.raises(RuntimeError):
            world_module.World("missing-campaign")
