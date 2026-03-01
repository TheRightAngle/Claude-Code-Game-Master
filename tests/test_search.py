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


def test_search_methods_handle_non_dict_root_shapes(tmp_path):
    ws, camp = make_world_state(tmp_path)
    (camp / "facts.json").write_text(json.dumps(["not-a-dict"], ensure_ascii=False))
    (camp / "npcs.json").write_text(json.dumps(["not-a-dict"], ensure_ascii=False))
    (camp / "locations.json").write_text(json.dumps(["not-a-dict"], ensure_ascii=False))
    (camp / "plots.json").write_text(json.dumps(["not-a-dict"], ensure_ascii=False))
    (camp / "consequences.json").write_text(json.dumps(["not-a-dict"], ensure_ascii=False))

    searcher = WorldSearcher(str(ws))

    assert searcher.search_facts("anything") == {}
    assert searcher.search_npcs("anything") == {}
    assert searcher.search_locations("anything") == {}
    assert searcher.search_plots("anything") == {}
    assert searcher.search_consequences("anything") == []


def test_search_facts_supports_string_fact_entries(tmp_path):
    ws, camp = make_world_state(tmp_path)
    (camp / "facts.json").write_text(
        json.dumps({"lore": ["Ancient dragon sleeps beneath the hills"]}, ensure_ascii=False)
    )

    searcher = WorldSearcher(str(ws))

    results = searcher.search_facts("dragon")

    assert results == {"lore": [{"fact": "Ancient dragon sleeps beneath the hills"}]}
