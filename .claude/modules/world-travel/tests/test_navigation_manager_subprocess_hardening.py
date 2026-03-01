#!/usr/bin/env python3
"""Tests for subprocess hardening in navigation_manager."""

import json
import sys
from pathlib import Path


MODULE_DIR = Path(__file__).parent.parent / "lib"
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MODULE_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from navigation_manager import NavigationManager


def test_move_resolves_bash_path_before_subprocess_run(monkeypatch, tmp_path):
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

    class FakeSessionManager:
        def move_party(self, location):
            return {"current_location": location}

    called = {}

    def fake_run(cmd, capture_output, text, check):
        called["cmd"] = cmd
        return type("RunResult", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr("navigation_manager.SessionManager", FakeSessionManager)
    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda executable: "/opt/bin/bash" if executable == "bash" else None)

    result = manager.move_with_navigation("Bravo")

    assert result["success"] is True
    assert called["cmd"][0] == "/opt/bin/bash"


def test_move_skips_survival_hook_when_bash_missing(monkeypatch, tmp_path, capsys):
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

    class FakeSessionManager:
        def move_party(self, location):
            return {"current_location": location}

    called = {"run_called": False}

    def fake_run(cmd, capture_output, text, check):
        called["run_called"] = True
        return type("RunResult", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr("navigation_manager.SessionManager", FakeSessionManager)
    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda executable: None if executable == "bash" else None)

    result = manager.move_with_navigation("Bravo")
    output = capsys.readouterr().out

    assert result["success"] is True
    assert called["run_called"] is False
    assert "bash executable not found" in output
