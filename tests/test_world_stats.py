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
