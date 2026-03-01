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


def test_search_npcs_by_tag_ignores_non_string_tag_entries(tmp_path):
    ws, camp = make_world_state(tmp_path)
    (camp / "npcs.json").write_text(
        json.dumps(
            {
                "Captain Rook": {
                    "tags": {
                        "locations": [None, 7, "Harbor Watch"],
                    }
                },
                "Broken Tags": {
                    "tags": {
                        "locations": [None, 12],
                    }
                },
            },
            ensure_ascii=False,
        )
    )

    searcher = WorldSearcher(str(ws))

    results = searcher.search_npcs_by_tag("location", "harbor")

    assert results == {
        "Captain Rook": {
            "tags": {
                "locations": [None, 7, "Harbor Watch"],
            }
        }
    }


def test_find_related_plots_ignores_non_string_list_entries(tmp_path):
    ws, camp = make_world_state(tmp_path)
    (camp / "plots.json").write_text(
        json.dumps(
            {
                "Roadside Ambush": {
                    "npcs": [None, 1, "Captain Rook"],
                    "locations": [{"name": "Forest Trail"}, "Harbor Road"],
                }
            },
            ensure_ascii=False,
        )
    )

    searcher = WorldSearcher(str(ws))

    related = searcher.find_related_plots("rook", entity_type="npc")

    assert "Roadside Ambush" in related


def test_getters_handle_malformed_root_payloads(tmp_path):
    ws, camp = make_world_state(tmp_path)
    (camp / "npcs.json").write_text(json.dumps(["not-a-dict"], ensure_ascii=False))
    (camp / "locations.json").write_text(json.dumps(["not-a-dict"], ensure_ascii=False))
    (camp / "facts.json").write_text(json.dumps(["not-a-dict"], ensure_ascii=False))
    (camp / "consequences.json").write_text(json.dumps(["not-a-dict"], ensure_ascii=False))

    searcher = WorldSearcher(str(ws))

    assert searcher.get_npc("Captain Rook") is None
    assert searcher.get_location("Town") is None
    assert searcher.get_pending_consequences() == []
    assert searcher.get_facts_by_category("lore") == []


def test_search_npcs_and_locations_tolerate_non_string_fields(tmp_path):
    ws, camp = make_world_state(tmp_path)
    (camp / "npcs.json").write_text(
        json.dumps(
            {
                "Captain Rook": {"description": 101, "attitude": "alert"},
            },
            ensure_ascii=False,
        )
    )
    (camp / "locations.json").write_text(
        json.dumps(
            {
                "Harbor Watch": {"description": 202, "position": 303},
            },
            ensure_ascii=False,
        )
    )

    searcher = WorldSearcher(str(ws))

    assert searcher.search_npcs("nomatch") == {}
    assert searcher.search_locations("nomatch") == {}


def test_print_results_tolerates_non_list_location_connections(tmp_path, capsys):
    ws, _ = make_world_state(tmp_path)
    searcher = WorldSearcher(str(ws))

    searcher.print_results(
        {
            "locations": {
                "Harbor Watch": {
                    "position": "North",
                    "description": "Gatehouse",
                    "connections": 7,
                }
            }
        }
    )

    output = capsys.readouterr().out
    assert "LOCATIONS" in output
