import json
import shutil
import subprocess
from pathlib import Path

from lib.time_manager import TimeManager


REPO_ROOT = Path(__file__).resolve().parents[1]


def _prepare_isolated_time_cli(tmp_path: Path) -> tuple[Path, Path, Path]:
    project_root = tmp_path / "project"
    tools_dir = project_root / "tools"
    campaign_dir = project_root / "world-state" / "campaigns" / "test-campaign"

    tools_dir.mkdir(parents=True, exist_ok=True)
    campaign_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(REPO_ROOT / "tools" / "dm-time.sh", tools_dir / "dm-time.sh")
    shutil.copy2(REPO_ROOT / "tools" / "common.sh", tools_dir / "common.sh")
    shutil.copytree(REPO_ROOT / "lib", project_root / "lib")

    (project_root / "world-state" / "active-campaign.txt").write_text("test-campaign")
    overview_path = campaign_dir / "campaign-overview.json"
    overview_path.write_text(
        json.dumps(
            {
                "campaign_name": "Test Campaign",
                "time_of_day": "Morning",
                "current_date": "Day 1",
                "time": {
                    "time_of_day": "Morning",
                    "current_date": "Day 1",
                    "calendar": "Default",
                },
            },
            ensure_ascii=False,
        )
    )

    return project_root, tools_dir / "dm-time.sh", overview_path


def test_dm_time_cli_works_from_non_repo_cwd(tmp_path: Path) -> None:
    project_root, time_script, overview_path = _prepare_isolated_time_cli(tmp_path)
    outside_cwd = tmp_path / "outside"
    outside_cwd.mkdir()

    result = subprocess.run(
        ["bash", str(time_script), "Night", "Day 2"],
        cwd=outside_cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0
    updated = json.loads(overview_path.read_text())
    assert updated["time_of_day"] == "Night"
    assert updated["current_date"] == "Day 2"
    assert updated["time"]["time_of_day"] == "Night"
    assert updated["time"]["current_date"] == "Day 2"


def test_dm_time_cli_joins_extra_date_tokens(tmp_path: Path) -> None:
    project_root, time_script, overview_path = _prepare_isolated_time_cli(tmp_path)
    outside_cwd = tmp_path / "outside"
    outside_cwd.mkdir()

    result = subprocess.run(
        ["bash", str(time_script), "Night", "16th", "day", "of", "Harvestmoon"],
        cwd=outside_cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0
    updated = json.loads(overview_path.read_text())
    assert updated["time_of_day"] == "Night"
    assert updated["current_date"] == "16th day of Harvestmoon"
    assert updated["time"]["time_of_day"] == "Night"
    assert updated["time"]["current_date"] == "16th day of Harvestmoon"


def make_world_state(tmp_path):
    ws = tmp_path / "world-state"
    camp = ws / "campaigns" / "test-campaign"
    camp.mkdir(parents=True)
    (ws / "active-campaign.txt").write_text("test-campaign")
    (camp / "campaign-overview.json").write_text(
        json.dumps(
            {
                "campaign_name": "Test Campaign",
                "time_of_day": "Morning",
                "current_date": "Day 1",
                "time": {
                    "time_of_day": "Morning",
                    "current_date": "Day 1",
                    "calendar": "Default",
                },
            },
            ensure_ascii=False,
        )
    )
    return ws, camp


def test_update_time_syncs_nested_and_top_level_fields(tmp_path):
    ws, camp = make_world_state(tmp_path)
    manager = TimeManager(str(ws))

    result = manager.update_time("Night", "Day 2")

    assert result
    data = json.loads((camp / "campaign-overview.json").read_text())
    assert data["time_of_day"] == "Night"
    assert data["current_date"] == "Day 2"
    assert data["time"]["time_of_day"] == "Night"
    assert data["time"]["current_date"] == "Day 2"
    assert data["time"]["calendar"] == "Default"


def test_time_manager_handles_non_dict_overview_payload(tmp_path):
    ws, camp = make_world_state(tmp_path)
    (camp / "campaign-overview.json").write_text(
        json.dumps(["not-a-dict"], ensure_ascii=False)
    )
    manager = TimeManager(str(ws))

    update_result = manager.update_time("Night", "Day 2")
    current_time = manager.get_time()

    assert update_result is False
    assert current_time == {"time_of_day": "Unknown", "current_date": "Unknown"}
