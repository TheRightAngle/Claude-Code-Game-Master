import json

from lib.world_stats import WorldStats


def make_world_state(tmp_path):
    ws = tmp_path / "world-state"
    camp = ws / "campaigns" / "test-campaign"
    camp.mkdir(parents=True)
    (ws / "active-campaign.txt").write_text("test-campaign")
    (camp / "campaign-overview.json").write_text(
        json.dumps(
            {
                "campaign_name": "Test Campaign",
                "player_position": {"current_location": "Town"},
                "time_of_day": "Morning",
                "current_date": "Day 1",
            },
            ensure_ascii=False,
        )
    )
    return ws, camp


def test_detailed_overview_handles_non_dict_consequences_file(tmp_path):
    ws, camp = make_world_state(tmp_path)
    (camp / "consequences.json").write_text(
        json.dumps(["not-a-dict"], ensure_ascii=False)
    )

    stats = WorldStats(str(ws))

    overview = stats.get_overview(detailed=True)

    assert "status" in overview
    assert "counts" in overview
    assert "details" in overview


def test_detailed_overview_ignores_malformed_entity_entries(tmp_path):
    ws, camp = make_world_state(tmp_path)
    (camp / "npcs.json").write_text(
        json.dumps(
            {"Scout": {"attitude": "friendly"}, "Broken NPC": "invalid"},
            ensure_ascii=False,
        )
    )
    (camp / "locations.json").write_text(
        json.dumps(
            {"Town Gate": {"connections": ["Inn"]}, "Broken Location": 7},
            ensure_ascii=False,
        )
    )
    (camp / "plots.json").write_text(
        json.dumps(
            {
                "Main Thread": {
                    "status": "active",
                    "type": "main",
                    "npcs": ["Scout"],
                    "locations": 99,
                },
                "Broken Plot": "invalid",
            },
            ensure_ascii=False,
        )
    )

    stats = WorldStats(str(ws))

    overview = stats.get_overview(detailed=True)

    assert overview["details"]["npcs"] == [{"name": "Scout", "attitude": "friendly"}]
    assert overview["details"]["locations"] == [{"name": "Town Gate", "connections": 1}]
    assert overview["details"]["active_plots"] == [
        {"name": "Main Thread", "type": "main", "npcs": 1, "locations": 0}
    ]
