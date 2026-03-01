#!/usr/bin/env python3
"""Tests for module_loader path defaults."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
MODULES_ROOT = PROJECT_ROOT / ".claude" / "modules"
sys.path.insert(0, str(MODULES_ROOT))

from module_loader import ModuleLoader


def test_default_project_root_is_repo_root():
    loader = ModuleLoader()
    assert loader.project_root.resolve() == PROJECT_ROOT.resolve()


def test_default_modules_dir_is_not_double_claude():
    loader = ModuleLoader()
    expected = PROJECT_ROOT / ".claude" / "modules"
    assert loader.modules_dir.resolve() == expected.resolve()
