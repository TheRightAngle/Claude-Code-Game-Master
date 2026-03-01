import json

from lib.time_manager import TimeManager


def make_world_state(tmp_path):
    ws = tmp_path / "world-state"
    camp = ws / "campaigns" / "test-campaign"
    camp.mkdir(parents=True)
    (ws / "active-campaign.txt").write_text("test-campaign")
    (camp / "campaign-overview.json").write_text(
        json.dumps(
            {
                "campaign_name": "Test Campaign",
                "time_of_day": "Morning",
                "current_date": "Day 1",
                "time": {
                    "time_of_day": "Morning",
                    "current_date": "Day 1",
                    "calendar": "Default",
                },
            },
            ensure_ascii=False,
        )
    )
    return ws, camp


def test_update_time_syncs_nested_and_top_level_fields(tmp_path):
    ws, camp = make_world_state(tmp_path)
    manager = TimeManager(str(ws))

    result = manager.update_time("Night", "Day 2")

    assert result
    data = json.loads((camp / "campaign-overview.json").read_text())
    assert data["time_of_day"] == "Night"
    assert data["current_date"] == "Day 2"
    assert data["time"]["time_of_day"] == "Night"
    assert data["time"]["current_date"] == "Day 2"
    assert data["time"]["calendar"] == "Default"
