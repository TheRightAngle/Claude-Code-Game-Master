import json
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


def _prepare_isolated_search_cli_runtime(tmp_path: Path) -> tuple[Path, Path]:
    project_root, search_script = _prepare_isolated_search_cli(tmp_path)
    shutil.copytree(REPO_ROOT / "lib", project_root / "lib")

    world_state_dir = project_root / "world-state"
    campaign_dir = world_state_dir / "campaigns" / "test-campaign"
    campaign_dir.mkdir(parents=True, exist_ok=True)
    (world_state_dir / "active-campaign.txt").write_text("test-campaign")
    (campaign_dir / "vectors").mkdir(parents=True, exist_ok=True)

    (campaign_dir / "facts.json").write_text(
        json.dumps(
            {
                "session_events": [
                    {"fact": "foo only", "timestamp": "2024-01-01T00:00:00Z"},
                    {"fact": "foo bar clue", "timestamp": "2024-01-01T00:01:00Z"},
                ]
            },
            ensure_ascii=False,
        )
    )
    (campaign_dir / "npcs.json").write_text(
        json.dumps(
            {
                "Guide Rowan": {
                    "description": "Local guide",
                    "attitude": "helpful",
                    "tags": {
                        "locations": ["Thornhaven"],
                        "quests": ["Missing Caravan"],
                    },
                }
            },
            ensure_ascii=False,
        )
    )
    (campaign_dir / "locations.json").write_text(json.dumps({}, ensure_ascii=False))
    (campaign_dir / "consequences.json").write_text(
        json.dumps({"active": []}, ensure_ascii=False)
    )
    (campaign_dir / "plots.json").write_text(json.dumps({}, ensure_ascii=False))

    tools_dir = project_root / "tools"
    dm_campaign_script = tools_dir / "dm-campaign.sh"
    dm_campaign_script.write_text(
        "#!/bin/bash\n"
        "if [ \"$1\" = \"path\" ]; then\n"
        "  echo \"$(cd \"$(dirname \"$0\")/..\" && pwd)/world-state/campaigns/test-campaign\"\n"
        "  exit 0\n"
        "fi\n"
        "exit 1\n"
    )

    return project_root, search_script


def _install_fast_entity_enhancer_stub(project_root: Path) -> None:
    (project_root / "lib" / "entity_enhancer.py").write_text(
        "import sys\n"
        "from campaign_manager import CampaignManager\n"
        "\n"
        "campaign_dir = CampaignManager('world-state').get_active_campaign_dir()\n"
        "if campaign_dir is None:\n"
        "    raise RuntimeError('No active campaign. Run /new-game or /import first.')\n"
        "\n"
        "if len(sys.argv) > 2 and sys.argv[1] == 'search':\n"
        "    print(f'RAG Search: {sys.argv[2]}')\n"
        "print('No passages found. Is the vector store populated?')\n",
        encoding="utf-8",
    )


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


def test_dm_search_rejects_conflicting_tag_filters(tmp_path: Path) -> None:
    project_root, search_script = _prepare_isolated_search_cli(tmp_path)

    result = subprocess.run(
        [
            "bash",
            str(search_script),
            "--tag-location",
            "Thornhaven",
            "--tag-quest",
            "Missing Caravan",
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=1,
    )

    assert result.returncode != 0
    assert "--tag-location and --tag-quest cannot be used together" in result.stderr
    assert "No active campaign" not in result.stderr


def test_dm_search_tag_mode_works_from_non_repo_cwd(tmp_path: Path) -> None:
    project_root, search_script = _prepare_isolated_search_cli_runtime(tmp_path)
    outside_cwd = tmp_path / "outside-tag"
    outside_cwd.mkdir()

    result = subprocess.run(
        ["bash", str(search_script), "--tag-location", "Thornhaven"],
        cwd=outside_cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0
    assert "Guide Rowan" in result.stdout


def test_dm_search_preserves_unquoted_multi_token_query(tmp_path: Path) -> None:
    project_root, search_script = _prepare_isolated_search_cli_runtime(tmp_path)
    outside_cwd = tmp_path / "outside-world"
    outside_cwd.mkdir()

    result = subprocess.run(
        ["bash", str(search_script), "foo", "bar", "--world-only"],
        cwd=outside_cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0
    assert "foo bar clue" in result.stdout
    assert "foo only" not in result.stdout


def test_dm_search_rag_mode_works_from_non_repo_cwd(tmp_path: Path) -> None:
    project_root, search_script = _prepare_isolated_search_cli_runtime(tmp_path)
    _install_fast_entity_enhancer_stub(project_root)
    outside_cwd = tmp_path / "outside-rag"
    outside_cwd.mkdir()

    result = subprocess.run(
        ["bash", str(search_script), "dragon", "--rag-only", "-n", "1"],
        cwd=outside_cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0
    assert "Source Material Matches" in result.stdout
    assert "No active campaign" not in combined_output
