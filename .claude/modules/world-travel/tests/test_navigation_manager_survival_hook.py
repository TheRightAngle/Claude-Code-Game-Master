#!/usr/bin/env python3
"""Tests for navigation_manager integration points."""

import json
import sys
from pathlib import Path

import pytest


MODULE_DIR = Path(__file__).parent.parent / "lib"
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MODULE_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from navigation_manager import NavigationManager


def test_move_uses_custom_stats_survival_hook(monkeypatch, tmp_path):
    campaign_dir = tmp_path / "campaign"
    campaign_dir.mkdir()

    (campaign_dir / "campaign-overview.json").write_text(json.dumps({
        "current_location": "Alpha",
        "player_position": {"current_location": "Alpha"},
        "time_of_day": "Evening",
        "current_date": "April 16th, 2012",
    }))
    (campaign_dir / "character.json").write_text(json.dumps({"speed_kmh": 4.0}))
    (campaign_dir / "locations.json").write_text(json.dumps({
        "Alpha": {
            "position": "A",
            "coordinates": {"x": 0, "y": 0},
            "connections": [{"to": "Bravo", "distance_meters": 1000, "terrain": "open"}],
        },
        "Bravo": {
            "position": "B",
            "coordinates": {"x": 1000, "y": 0},
            "connections": [],
        },
    }))

    manager = NavigationManager(str(campaign_dir))

    class FakeSessionManager:
        def move_party(self, location):
            return {"current_location": location}

    called = {}

    def fake_run(cmd, capture_output, text, check):
        called["cmd"] = cmd
        return type("RunResult", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr("navigation_manager.SessionManager", FakeSessionManager)
    monkeypatch.setattr("subprocess.run", fake_run)

    result = manager.move_with_navigation("Bravo")

    assert result["success"] is True
    assert "cmd" in called
    assert "custom-stats/tools/dm-survival.sh" in called["cmd"][1]
    assert "survival-stats" not in called["cmd"][1]
    assert called["cmd"][2:7] == [
        "time",
        "Evening",
        "April 16th, 2012",
        "--elapsed",
        "0.25",
    ]


@pytest.mark.parametrize("speed_multiplier", [0, -1.0])
def test_move_rejects_non_positive_speed_multiplier(monkeypatch, tmp_path, speed_multiplier):
    campaign_dir = tmp_path / "campaign"
    campaign_dir.mkdir()

    (campaign_dir / "campaign-overview.json").write_text(json.dumps({
        "current_location": "Alpha",
        "player_position": {"current_location": "Alpha"},
    }))
    (campaign_dir / "character.json").write_text(json.dumps({"speed_kmh": 4.0}))
    (campaign_dir / "locations.json").write_text(json.dumps({
        "Alpha": {
            "position": "A",
            "coordinates": {"x": 0, "y": 0},
            "connections": [{"to": "Bravo", "distance_meters": 1000, "terrain": "open"}],
        },
        "Bravo": {
            "position": "B",
            "coordinates": {"x": 1000, "y": 0},
            "connections": [],
        },
    }))

    manager = NavigationManager(str(campaign_dir))

    class FailSessionManager:
        def move_party(self, location):
            raise AssertionError("move_party should not be called for invalid speed multiplier")

    def fail_run(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called for invalid speed multiplier")

    monkeypatch.setattr("navigation_manager.SessionManager", FailSessionManager)
    monkeypatch.setattr("subprocess.run", fail_run)

    result = manager.move_with_navigation("Bravo", speed_multiplier=speed_multiplier)

    assert result == {
        "success": False,
        "error": "speed_multiplier must be greater than 0",
    }


def test_move_suppresses_session_stdout_when_emit_logs_false(monkeypatch, tmp_path, capsys):
    campaign_dir = tmp_path / "campaign"
    campaign_dir.mkdir()

    (campaign_dir / "campaign-overview.json").write_text(json.dumps({
        "current_location": "Alpha",
        "player_position": {"current_location": "Alpha"},
    }))
    (campaign_dir / "character.json").write_text(json.dumps({"speed_kmh": 4.0}))
    (campaign_dir / "locations.json").write_text(json.dumps({
        "Alpha": {
            "position": "A",
            "coordinates": {"x": 0, "y": 0},
            "connections": [{"to": "Bravo", "distance_meters": 1000, "terrain": "open"}],
        },
        "Bravo": {
            "position": "B",
            "coordinates": {"x": 1000, "y": 0},
            "connections": [],
        },
    }))

    manager = NavigationManager(str(campaign_dir))

    class NoisySessionManager:
        def move_party(self, location):
            print("[SESSION] move_party wrote to stdout")
            return {"current_location": location}

    def fake_run(cmd, capture_output, text, check):
        return type("RunResult", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr("navigation_manager.SessionManager", NoisySessionManager)
    monkeypatch.setattr("subprocess.run", fake_run)

    result = manager.move_with_navigation("Bravo", emit_logs=False)
    output = capsys.readouterr().out

    assert result["success"] is True
    assert output == ""
