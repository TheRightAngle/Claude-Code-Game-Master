
import json

from lib.session_manager import SessionManager


def make_world_state(tmp_path, overview_extra=None, with_character=True):
    ws = tmp_path / "world-state"
    camp = ws / "campaigns" / "test-campaign"
    camp.mkdir(parents=True)
    (ws / "active-campaign.txt").write_text("test-campaign")

    overview = {
        "campaign_name": "Test Campaign",
        "time_of_day": "Day",
        "current_date": "Day 1",
        "current_character": "Hero",
    }
    if overview_extra:
        overview.update(overview_extra)
    (camp / "campaign-overview.json").write_text(
        json.dumps(overview, ensure_ascii=False)
    )

    if with_character:
        character = {
            "name": "Hero",
            "level": 1,
            "hp": {"current": 20, "max": 20},
            "gold": 100,
        }
        (camp / "character.json").write_text(
            json.dumps(character, ensure_ascii=False)
        )

    (camp / "locations.json").write_text("{}")
    (camp / "npcs.json").write_text("{}")
    (camp / "facts.json").write_text("{}")
    (camp / "consequences.json").write_text("{}")
    (camp / "plots.json").write_text("{}")
    (camp / "items.json").write_text("{}")

    return str(ws), camp


class TestMoveParty:
    def test_move_updates_current_location(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        result = mgr.move_party("Tavern")
        assert result["current_location"] == "Tavern"

    def test_move_records_previous_location(self, tmp_path):
        ws, camp = make_world_state(tmp_path, overview_extra={
            "player_position": {"current_location": "Forest"}
        })
        mgr = SessionManager(ws)
        result = mgr.move_party("Castle")
        assert result["previous_location"] == "Forest"

    def test_move_persists_to_campaign_file(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        mgr.move_party("Dungeon")
        data = json.loads((camp / "campaign-overview.json").read_text())
        assert data["player_position"]["current_location"] == "Dungeon"

    def test_move_updates_character_location(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        mgr.move_party("Marketplace")
        char = json.loads((camp / "character.json").read_text())
        assert char["current_location"] == "Marketplace"

    def test_move_auto_creates_location_in_locations_json(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        mgr.move_party("New Place")
        locations = json.loads((camp / "locations.json").read_text())
        assert "New Place" in locations

    def test_move_creates_bidirectional_connection(self, tmp_path):
        ws, camp = make_world_state(tmp_path, overview_extra={
            "player_position": {"current_location": "Town"}
        })
        locs = {"Town": {"connections": [], "position": "center", "description": ""}}
        (camp / "locations.json").write_text(json.dumps(locs))

        mgr = SessionManager(ws)
        mgr.move_party("Forest")

        locations = json.loads((camp / "locations.json").read_text())
        town_connections = [c["to"] for c in locations["Town"].get("connections", [])]
        assert "Forest" in town_connections
        forest_connections = [c["to"] for c in locations["Forest"].get("connections", [])]
        assert "Town" in forest_connections

    def test_move_handles_malformed_connection_entries(self, tmp_path):
        ws, camp = make_world_state(tmp_path, overview_extra={
            "player_position": {"current_location": "Town"}
        })
        (camp / "locations.json").write_text(
            json.dumps(
                {
                    "Town": {
                        "connections": ["bad-entry", {"path": "unknown"}, {"to": "Road"}],
                        "position": "center",
                        "description": ""
                    }
                },
                ensure_ascii=False,
            )
        )

        mgr = SessionManager(ws)
        mgr.move_party("Forest")

        locations = json.loads((camp / "locations.json").read_text())
        town_targets = [
            c.get("to")
            for c in locations["Town"].get("connections", [])
            if isinstance(c, dict)
        ]
        assert "Forest" in town_targets


class TestGetContext:
    def test_get_full_context_returns_string(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        ctx = mgr.get_full_context()
        assert isinstance(ctx, str)
        assert len(ctx) > 0

    def test_get_full_context_contains_campaign_name(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        ctx = mgr.get_full_context()
        assert "Test Campaign" in ctx

    def test_get_full_context_contains_character_info(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        ctx = mgr.get_full_context()
        assert "Hero" in ctx

    def test_get_status_returns_dict(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        status = mgr.get_status()
        assert isinstance(status, dict)
        assert "locations_count" in status
        assert "npcs_count" in status

    def test_get_full_context_reads_pending_consequences_from_active_schema(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        (camp / "consequences.json").write_text(
            json.dumps(
                {
                    "active": [
                        {
                            "id": "abcd1234",
                            "consequence": "Storm cuts off the mountain pass",
                            "trigger": "at dusk",
                        }
                    ],
                    "resolved": [],
                },
                ensure_ascii=False,
            )
        )
        mgr = SessionManager(ws)

        ctx = mgr.get_full_context()
        assert "Storm cuts off the mountain pass" in ctx
        assert "at dusk" in ctx

    def test_get_full_context_handles_non_dict_player_position_and_time(self, tmp_path):
        ws, camp = make_world_state(
            tmp_path,
            overview_extra={
                "player_position": ["invalid-shape"],
                "time": "invalid-shape",
            },
        )
        mgr = SessionManager(ws)

        ctx = mgr.get_full_context()

        assert "Test Campaign" in ctx
        assert "Location: Unknown | Time: Day, Day 1" in ctx


class TestSavePathTraversal:
    def test_create_save_sanitizes_slashes_in_name(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)

        filename = mgr.create_save("Chapter/One")

        assert "/" not in filename
        assert "\\" not in filename
        assert (camp / "saves" / filename).exists()

    def test_restore_save_rejects_traversal_name(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        outside_file = camp / "outside-save.json"
        outside_file.write_text(json.dumps({"snapshot": {}}, ensure_ascii=False))

        mgr = SessionManager(ws)
        assert mgr.restore_save("../outside-save.json") is False

    def test_delete_save_rejects_traversal_name(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        outside_file = camp / "outside-save.json"
        outside_file.write_text(json.dumps({"snapshot": {}}, ensure_ascii=False))

        mgr = SessionManager(ws)
        assert mgr.delete_save("../outside-save.json") is False
        assert outside_file.exists()

    def test_restore_save_returns_false_when_snapshot_write_fails(self, tmp_path, monkeypatch):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        original_overview = json.loads((camp / "campaign-overview.json").read_text())
        original_locations = json.loads((camp / "locations.json").read_text())

        save_file = camp / "saves" / "bad-write.json"
        save_file.parent.mkdir(parents=True, exist_ok=True)
        save_file.write_text(
            json.dumps(
                {
                    "snapshot": {
                        "campaign_overview": {"campaign_name": "Recovered"},
                        "locations": {"Town": {"connections": []}}
                    }
                },
                ensure_ascii=False,
            )
        )

        real_save_json = mgr.json_ops.save_json

        def fail_locations(filename, data, indent=2):
            if filename == "locations.json":
                return False
            return real_save_json(filename, data, indent=indent)

        monkeypatch.setattr(mgr.json_ops, "save_json", fail_locations)

        assert mgr.restore_save("bad-write") is False
        assert json.loads((camp / "campaign-overview.json").read_text()) == original_overview
        assert json.loads((camp / "locations.json").read_text()) == original_locations

    def test_create_and_restore_save_round_trips_plots_and_items(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)

        original_plots = {"main_arc": {"status": "active", "chapter": 2}}
        original_items = {"healing_potion": {"quantity": 3, "rarity": "common"}}
        (camp / "plots.json").write_text(json.dumps(original_plots, ensure_ascii=False))
        (camp / "items.json").write_text(json.dumps(original_items, ensure_ascii=False))

        filename = mgr.create_save("with-plots-items")

        (camp / "plots.json").write_text(json.dumps({"main_arc": {"status": "completed"}}, ensure_ascii=False))
        (camp / "items.json").write_text(json.dumps({"healing_potion": {"quantity": 0}}, ensure_ascii=False))

        assert mgr.restore_save(filename) is True
        assert json.loads((camp / "plots.json").read_text()) == original_plots
        assert json.loads((camp / "items.json").read_text()) == original_items

    def test_restore_save_rolls_back_if_backup_capture_fails_after_prior_write(self, tmp_path, monkeypatch):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        original_overview = json.loads((camp / "campaign-overview.json").read_text())

        save_file = camp / "saves" / "backup-capture-fail.json"
        save_file.parent.mkdir(parents=True, exist_ok=True)
        save_file.write_text(
            json.dumps(
                {
                    "snapshot": {
                        "campaign_overview": {"campaign_name": "Should Roll Back"},
                        "npcs": {"Guard": {"is_party_member": False}},
                    }
                },
                ensure_ascii=False,
            )
        )

        real_capture = mgr._capture_file_state

        def fail_on_npcs(filepath):
            if filepath.name == "npcs.json":
                return None
            return real_capture(filepath)

        monkeypatch.setattr(mgr, "_capture_file_state", fail_on_npcs)

        assert mgr.restore_save("backup-capture-fail") is False
        assert json.loads((camp / "campaign-overview.json").read_text()) == original_overview


class TestSessionStartEnd:
    def test_start_session_returns_summary(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        summary = mgr.start_session()
        assert isinstance(summary, dict)
        assert "timestamp" in summary

    def test_start_session_creates_log(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        mgr.start_session()
        log = camp / "session-log.md"
        assert log.exists()
        assert "Session Started:" in log.read_text()

    def test_end_session_logs_summary(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        mgr.start_session()
        mgr.end_session("Fought dragons and won")
        log = (camp / "session-log.md").read_text()
        assert "Fought dragons and won" in log

    def test_end_session_increments_session_count_in_campaign_overview(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)

        mgr.start_session()
        mgr.end_session("Summary one")

        overview = json.loads((camp / "campaign-overview.json").read_text())
        assert overview["session_count"] == 1

    def test_end_session_rollback_when_counter_persist_fails(self, tmp_path, monkeypatch):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        mgr.start_session()

        original_log = (camp / "session-log.md").read_text()
        original_overview = json.loads((camp / "campaign-overview.json").read_text())
        real_save_json = mgr.json_ops.save_json

        def fail_campaign_overview(filename, data, indent=2):
            if filename == "campaign-overview.json":
                return False
            return real_save_json(filename, data, indent=indent)

        monkeypatch.setattr(mgr.json_ops, "save_json", fail_campaign_overview)

        assert mgr.end_session("This should rollback") is False
        assert (camp / "session-log.md").read_text() == original_log
        assert json.loads((camp / "campaign-overview.json").read_text()) == original_overview

    def test_end_session_syncs_campaign_counter_to_log_session_number(self, tmp_path):
        ws, camp = make_world_state(tmp_path, overview_extra={"session_count": 99})
        mgr = SessionManager(ws)

        mgr.start_session()
        assert mgr.end_session("Summary one") is True

        overview = json.loads((camp / "campaign-overview.json").read_text())
        assert overview["session_count"] == mgr._get_session_number()
        assert overview["session_count"] == 1

    def test_session_count_increments(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        mgr.start_session()
        assert mgr._get_session_number() == 1
        mgr.start_session()
        assert mgr._get_session_number() == 2
