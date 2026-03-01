#!/usr/bin/env python3
"""Tests for inventory_manager.py."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

MODULE_LIB = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(MODULE_LIB))
from inventory_manager import InventoryManager


@pytest.fixture
def fake_campaign(tmp_path):
    world_state = tmp_path / "world-state"
    campaign_dir = world_state / "campaigns" / "test-campaign"
    campaign_dir.mkdir(parents=True)

    (world_state / "active-campaign.txt").write_text("test-campaign")

    (campaign_dir / "campaign-overview.json").write_text(
        json.dumps(
            {
                "campaign_name": "Test Campaign",
                "current_character": "Test Hero",
            },
            indent=2,
        )
    )
    (campaign_dir / "character.json").write_text(
        json.dumps(
            {
                "name": "Test Hero",
                "gold": 100,
                "hp": {"current": 10, "max": 10},
                "xp": {"current": 0, "next_level": 100},
                "inventory": {
                    "stackable": {"Bandage": 3},
                    "unique": [],
                },
                "custom_stats": {},
            },
            indent=2,
        )
    )

    return {"world_state": world_state, "campaign_dir": campaign_dir, "cwd": tmp_path}


def _run_inventory_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    manager_script = Path(__file__).parent.parent / "lib" / "inventory_manager.py"
    command = [sys.executable, str(manager_script), *args]
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_remove_negative_quantity_is_rejected(fake_campaign):
    manager = InventoryManager(fake_campaign["campaign_dir"])

    success = manager.apply_transaction({"remove": {"Bandage": -1}}, test_mode=True)

    assert success is False


def test_cli_rejects_character_name_mismatch(fake_campaign):
    result = _run_inventory_cli(fake_campaign["cwd"], "show", "Not Active Hero")

    assert result.returncode == 1
    assert "does not match active character" in result.stderr
