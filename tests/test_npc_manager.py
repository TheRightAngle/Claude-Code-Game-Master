import json

import pytest

from lib.npc_manager import NPCManager


def make_world_state(tmp_path, npcs):
    ws = tmp_path / "world-state"
    camp = ws / "campaigns" / "test-campaign"
    camp.mkdir(parents=True)
    (ws / "active-campaign.txt").write_text("test-campaign")
    (camp / "campaign-overview.json").write_text(
        json.dumps({"campaign_name": "Test Campaign"}, ensure_ascii=False)
    )
    (camp / "npcs.json").write_text(json.dumps(npcs, ensure_ascii=False))
    return str(ws)


def test_list_npcs_handles_legacy_tags_list_with_filters(tmp_path):
    ws = make_world_state(
        tmp_path,
        {
            "Old Guard": {
                "description": "Legacy NPC",
                "attitude": "neutral",
                "tags": ["market", "side-quest"],
            }
        },
    )
    mgr = NPCManager(ws)

    by_location = mgr.list_npcs(filter_location="market")
    by_quest = mgr.list_npcs(filter_quest="side-quest")

    assert "Old Guard" in by_location
    assert "Old Guard" in by_quest


@pytest.mark.parametrize(
    "character_sheet",
    [
        {"level": 2},
        {"hp": "not-a-dict"},
    ],
)
def test_set_npc_stat_hp_max_fails_gracefully_for_malformed_hp(tmp_path, character_sheet):
    ws = make_world_state(
        tmp_path,
        {
            "Aela": {
                "description": "Party member",
                "attitude": "friendly",
                "is_party_member": True,
                "character_sheet": character_sheet,
            }
        },
    )
    mgr = NPCManager(ws)

    result = mgr.set_npc_stat("Aela", "hp_max", "25")

    assert result is False
