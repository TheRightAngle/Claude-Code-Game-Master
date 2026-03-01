from lib.agent_extractor import AgentExtractor


def test_validate_and_save_treats_save_json_false_as_error(tmp_path, monkeypatch):
    ws = tmp_path / "world-state"
    extractor = AgentExtractor(str(ws), campaign_name="test-campaign")

    merged_data = {
        "npcs": {
            "Kara": {
                "description": "A sharp-eyed scout",
                "attitude": "ally",
                "events": [],
                "location_tags": [],
                "quest_tags": [],
            }
        },
        "locations": {},
        "items": {},
        "plot_hooks": {},
        "metadata": {"document_name": "module"},
    }

    def fail_save(self, filename, data, indent=2):
        return False

    monkeypatch.setattr("lib.agent_extractor.JsonOperations.save_json", fail_save)

    results = extractor.validate_and_save(merged_data)

    assert results["npcs_saved"] == 0
    assert any("Failed to save NPCs" in msg for msg in results["errors"])
