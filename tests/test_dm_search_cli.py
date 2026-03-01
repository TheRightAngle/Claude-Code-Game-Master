import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _prepare_isolated_search_cli(tmp_path: Path) -> tuple[Path, Path]:
    project_root = tmp_path / "project"
    tools_dir = project_root / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(REPO_ROOT / "tools" / "dm-search.sh", tools_dir / "dm-search.sh")
    shutil.copy2(REPO_ROOT / "tools" / "common.sh", tools_dir / "common.sh")

    return project_root, tools_dir / "dm-search.sh"


def test_dm_search_rejects_world_only_and_rag_only_together(tmp_path: Path) -> None:
    project_root, search_script = _prepare_isolated_search_cli(tmp_path)

    result = subprocess.run(
        ["bash", str(search_script), "dragon", "--world-only", "--rag-only"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--world-only and --rag-only cannot be used together" in result.stderr


def test_dm_search_rejects_missing_value_for_n_option(tmp_path: Path) -> None:
    project_root, search_script = _prepare_isolated_search_cli(tmp_path)

    result = subprocess.run(
        ["bash", str(search_script), "dragon", "-n"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=1,
    )

    assert result.returncode != 0
    assert "Missing value for -n" in result.stderr


def test_dm_search_rejects_missing_value_for_tag_location_option(tmp_path: Path) -> None:
    project_root, search_script = _prepare_isolated_search_cli(tmp_path)

    result = subprocess.run(
        ["bash", str(search_script), "--tag-location"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=1,
    )

    assert result.returncode != 0
    assert "Missing value for --tag-location" in result.stderr


def test_dm_search_rejects_missing_value_for_tag_quest_option(tmp_path: Path) -> None:
    project_root, search_script = _prepare_isolated_search_cli(tmp_path)

    result = subprocess.run(
        ["bash", str(search_script), "--tag-quest"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=1,
    )

    assert result.returncode != 0
    assert "Missing value for --tag-quest" in result.stderr


def test_dm_search_rejects_unknown_flag_with_actionable_error(tmp_path: Path) -> None:
    project_root, search_script = _prepare_isolated_search_cli(tmp_path)

    result = subprocess.run(
        ["bash", str(search_script), "dragon", "--bogus"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=1,
    )

    assert result.returncode != 0
    assert "Unknown option: --bogus" in result.stderr
    assert "No active campaign" not in result.stderr


def test_dm_search_rejects_non_integer_n_before_campaign_checks(tmp_path: Path) -> None:
    project_root, search_script = _prepare_isolated_search_cli(tmp_path)

    result = subprocess.run(
        ["bash", str(search_script), "dragon", "-n", "foo"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=1,
    )

    assert result.returncode != 0
    assert "Invalid value for -n" in result.stderr
    assert "integer >= 0" in result.stderr
    assert "No active campaign" not in result.stderr
