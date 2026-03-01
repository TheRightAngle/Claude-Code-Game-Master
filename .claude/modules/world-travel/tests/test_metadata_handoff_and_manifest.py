#!/usr/bin/env python3
"""Tests for world-travel metadata handoff and manifest command metadata."""

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def test_dm_session_move_uses_json_handoff_for_encounter_metadata(tmp_path):
    project_root = tmp_path / "repo"
    module_dir = project_root / ".claude" / "modules" / "world-travel"
    middleware_dir = module_dir / "middleware"
    tools_dir = module_dir / "tools"
    middleware_dir.mkdir(parents=True)
    tools_dir.mkdir(parents=True)

    source_middleware = Path(__file__).parent.parent / "middleware" / "dm-session.sh"
    test_middleware = middleware_dir / "dm-session.sh"
    shutil.copy(source_middleware, test_middleware)
    test_middleware.chmod(test_middleware.stat().st_mode | stat.S_IEXEC)

    _write_executable(
        tools_dir / "dm-navigation.sh",
        """#!/usr/bin/env bash
printf '%s\\n' "$@" > "$NAV_ARGS_FILE"
if [[ " $* " == *" --json "* ]]; then
  echo '{"success": true, "location": "Forest", "distance_meters": 900, "terrain": "swamp"}'
else
  echo "[SUCCESS] Moved to: Forest"
fi
exit 0
""",
    )
    _write_executable(
        tools_dir / "dm-encounter.sh",
        """#!/usr/bin/env bash
printf '%s\\n' "$@" > "$ENCOUNTER_ARGS_FILE"
exit 0
""",
    )

    nav_args_file = tmp_path / "nav-args.txt"
    encounter_args_file = tmp_path / "encounter-args.txt"
    env = os.environ.copy()
    env["NAV_ARGS_FILE"] = str(nav_args_file)
    env["ENCOUNTER_ARGS_FILE"] = str(encounter_args_file)

    result = subprocess.run(
        ["bash", str(test_middleware), "move", "Forest"],
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    nav_args = nav_args_file.read_text(encoding="utf-8")
    assert "--json" in nav_args
    encounter_args = encounter_args_file.read_text(encoding="utf-8").strip().split()
    assert encounter_args[-2:] == ["900", "swamp"]


def test_dm_session_move_parses_json_even_with_navigation_preamble(tmp_path):
    project_root = tmp_path / "repo"
    module_dir = project_root / ".claude" / "modules" / "world-travel"
    middleware_dir = module_dir / "middleware"
    tools_dir = module_dir / "tools"
    middleware_dir.mkdir(parents=True)
    tools_dir.mkdir(parents=True)

    source_middleware = Path(__file__).parent.parent / "middleware" / "dm-session.sh"
    test_middleware = middleware_dir / "dm-session.sh"
    shutil.copy(source_middleware, test_middleware)
    test_middleware.chmod(test_middleware.stat().st_mode | stat.S_IEXEC)

    _write_executable(
        tools_dir / "dm-navigation.sh",
        """#!/usr/bin/env bash
printf '%s\\n' "$@" > "$NAV_ARGS_FILE"
echo "[SESSION] current_location updated"
echo '{"success": true, "location": "Forest", "distance_meters": 1200, "terrain": "open"}'
exit 0
""",
    )
    _write_executable(
        tools_dir / "dm-encounter.sh",
        """#!/usr/bin/env bash
printf '%s\\n' "$@" > "$ENCOUNTER_ARGS_FILE"
exit 0
""",
    )

    nav_args_file = tmp_path / "nav-args-preamble.txt"
    encounter_args_file = tmp_path / "encounter-args-preamble.txt"
    env = os.environ.copy()
    env["NAV_ARGS_FILE"] = str(nav_args_file)
    env["ENCOUNTER_ARGS_FILE"] = str(encounter_args_file)

    result = subprocess.run(
        ["bash", str(test_middleware), "move", "Forest"],
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    encounter_args = encounter_args_file.read_text(encoding="utf-8").strip().split()
    assert encounter_args[-2:] == ["1200", "open"]


def test_world_travel_manifest_uses_routes_command_metadata():
    manifest_path = Path(__file__).parent.parent / "module.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    commands = manifest["adds_to_core"]["commands"]

    assert "dm-navigation.sh routes <from> <to>" in commands
    assert "dm-navigation.sh route <from> <to>" not in commands
