import json

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
