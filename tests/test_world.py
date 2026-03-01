import json

import lib.world as world_module
import pytest
from lib.campaign_manager import CampaignManager


def make_world_state(tmp_path):
    ws = tmp_path / "world-state"
    campaigns_dir = ws / "campaigns"
    campaigns_dir.mkdir(parents=True)

    def seed_campaign(name, location):
        camp = campaigns_dir / name
        camp.mkdir()
        (camp / "campaign-overview.json").write_text(
            json.dumps(
                {
                    "campaign_name": f"{name.title()} Campaign",
                    "time_of_day": "Day",
                    "current_date": "Day 1",
                    "player_position": {"current_location": location},
                },
                ensure_ascii=False,
            )
        )
        (camp / "npcs.json").write_text("{}")
        (camp / "locations.json").write_text("{}")
        (camp / "plots.json").write_text("{}")
        (camp / "facts.json").write_text("{}")
        (camp / "consequences.json").write_text(
            json.dumps({"active": [], "resolved": []}, ensure_ascii=False)
        )
        (camp / "character.json").write_text(
            json.dumps({"name": "Hero", "hp": {"current": 10, "max": 10}}, ensure_ascii=False)
        )
        return camp

    alpha = seed_campaign("alpha", "Alpha Town")
    beta = seed_campaign("beta", "Beta Town")
    (ws / "active-campaign.txt").write_text("alpha")
    return ws, alpha, beta


def configure_world_campaign_manager(monkeypatch, ws):
    monkeypatch.setattr(
        world_module,
        "CampaignManager",
        lambda: CampaignManager(str(ws)),
    )


def test_get_status_handles_non_dict_player_position(tmp_path, monkeypatch):
    ws, alpha, beta = make_world_state(tmp_path)
    configure_world_campaign_manager(monkeypatch, ws)

    (alpha / "campaign-overview.json").write_text(
        json.dumps(
            {
                "campaign_name": "Alpha Campaign",
                "time_of_day": "Day",
                "current_date": "Day 1",
                "player_position": ["invalid-shape"],
            },
            ensure_ascii=False,
        )
    )

    world = world_module.World("alpha")
    status = world.get_status()

    assert status["campaign"] == "alpha"
    assert status["location"] is None


def test_get_status_handles_legacy_consequences_list(tmp_path, monkeypatch):
    ws, alpha, beta = make_world_state(tmp_path)
    configure_world_campaign_manager(monkeypatch, ws)

    (alpha / "consequences.json").write_text(
        json.dumps(
            [
                {"id": "c1", "consequence": "Storm rolls in"},
                {"id": "c2", "consequence": "Bridge collapses"},
            ],
            ensure_ascii=False,
        )
    )

    world = world_module.World("alpha")
    status = world.get_status()

    assert status["campaign"] == "alpha"
    assert status["active_consequences"] == 2


def test_world_managers_stay_pinned_to_selected_campaign(tmp_path, monkeypatch):
    ws, alpha, beta = make_world_state(tmp_path)
    configure_world_campaign_manager(monkeypatch, ws)

    world = world_module.World("alpha")

    global_campaigns = CampaignManager(str(ws))
    assert global_campaigns.set_active("beta") is True

    assert world.npcs.create_npc("Pinned Ally", "Works for alpha", "friendly") is True
    assert world.locations.add_location("Alpha Keep", "hilltop") is True
    assert global_campaigns.get_active() == "beta"

    alpha_npcs = json.loads((alpha / "npcs.json").read_text())
    beta_npcs = json.loads((beta / "npcs.json").read_text())
    alpha_locations = json.loads((alpha / "locations.json").read_text())
    beta_locations = json.loads((beta / "locations.json").read_text())

    assert "Pinned Ally" in alpha_npcs
    assert "Pinned Ally" not in beta_npcs
    assert "Alpha Keep" in alpha_locations
    assert "Alpha Keep" not in beta_locations


def test_create_pinned_manager_raises_when_switch_to_pinned_campaign_fails(tmp_path, monkeypatch):
    ws, alpha, beta = make_world_state(tmp_path)
    configure_world_campaign_manager(monkeypatch, ws)

    world = world_module.World("alpha")
    global_campaigns = CampaignManager(str(ws))
    assert global_campaigns.set_active("beta") is True

    real_set_active = world.campaign_mgr.set_active

    def fail_switch_to_alpha(name):
        if name == "alpha":
            return False
        return real_set_active(name)

    monkeypatch.setattr(world.campaign_mgr, "set_active", fail_switch_to_alpha)

    with pytest.raises(RuntimeError, match="Failed to set active campaign to pinned campaign 'alpha'"):
        _ = world.npcs

    assert world._npcs is None
    assert global_campaigns.get_active() == "beta"
