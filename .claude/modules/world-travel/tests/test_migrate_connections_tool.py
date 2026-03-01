#!/usr/bin/env python3
"""Tests for migrate-connections tool helpers."""

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
SCRIPT_PATH = PROJECT_ROOT / ".claude" / "modules" / "world-travel" / "tools" / "migrate-connections.py"


def load_module():
    spec = importlib.util.spec_from_file_location("migrate_connections", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_campaigns_dir_points_to_project_world_state():
    module = load_module()
    assert module.get_campaigns_dir() == PROJECT_ROOT / "world-state" / "campaigns"
