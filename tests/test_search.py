import json

from lib.search import WorldSearcher


def make_world_state(tmp_path):
    ws = tmp_path / "world-state"
    camp = ws / "campaigns" / "test-campaign"
    camp.mkdir(parents=True)
    (ws / "active-campaign.txt").write_text("test-campaign")
    (camp / "campaign-overview.json").write_text(
        json.dumps({"campaign_name": "Test Campaign"}, ensure_ascii=False)
    )
    return ws, camp


def test_search_plots_ignores_non_string_list_items(tmp_path):
    ws, camp = make_world_state(tmp_path)
    (camp / "plots.json").write_text(
        json.dumps(
            {
                "Ambush": {
                    "description": "Bandits are waiting in the trees",
                    "npcs": [42, "Captain Rook"],
                    "locations": ["Forest Road", {"name": "Crossing"}],
                    "objectives": [None, "Protect the caravan"],
                }
            },
            ensure_ascii=False,
        )
    )

    searcher = WorldSearcher(str(ws))

    results = searcher.search_plots("rook")

    assert "Ambush" in results
