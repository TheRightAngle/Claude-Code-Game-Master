import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _prepare_isolated_player_cli(tmp_path: Path) -> tuple[Path, Path]:
    project_root = tmp_path / "project"
    tools_dir = project_root / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(REPO_ROOT / "tools" / "dm-player.sh", tools_dir / "dm-player.sh")
    shutil.copy2(REPO_ROOT / "tools" / "common.sh", tools_dir / "common.sh")

    return project_root, tools_dir / "dm-player.sh"


def test_dm_player_unknown_action_exits_non_zero_and_shows_usage(tmp_path: Path) -> None:
    project_root, player_script = _prepare_isolated_player_cli(tmp_path)

    result = subprocess.run(
        ["bash", str(player_script), "bogus-action"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=1,
    )

    assert result.returncode != 0
    assert "Usage: dm-player.sh <action> [args]" in result.stdout
    assert "No active campaign" not in result.stderr


def test_dm_player_help_is_accessible_without_active_campaign(tmp_path: Path) -> None:
    project_root, player_script = _prepare_isolated_player_cli(tmp_path)

    result = subprocess.run(
        ["bash", str(player_script), "--help"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=1,
    )

    assert result.returncode == 0
    assert "Usage: dm-player.sh <action> [args]" in result.stdout
    assert "No active campaign" not in result.stderr


def test_dm_player_usage_without_args_is_accessible_without_active_campaign(
    tmp_path: Path,
) -> None:
    project_root, player_script = _prepare_isolated_player_cli(tmp_path)

    result = subprocess.run(
        ["bash", str(player_script)],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=1,
    )

    assert "Usage: dm-player.sh <action> [args]" in result.stdout
    assert "No active campaign" not in result.stderr
