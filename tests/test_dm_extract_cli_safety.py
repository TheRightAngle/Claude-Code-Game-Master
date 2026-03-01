import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _prepare_isolated_extract_cli(tmp_path: Path) -> tuple[Path, Path]:
    project_root = tmp_path / "project"
    tools_dir = project_root / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(REPO_ROOT / "tools" / "dm-extract.sh", tools_dir / "dm-extract.sh")
    shutil.copy2(REPO_ROOT / "tools" / "common.sh", tools_dir / "common.sh")

    return project_root, tools_dir / "dm-extract.sh"


def test_clean_campaign_removes_only_extraction_artifacts(tmp_path: Path) -> None:
    project_root, extract_script = _prepare_isolated_extract_cli(tmp_path)
    (project_root / "world-state").mkdir(parents=True, exist_ok=True)
    (project_root / "world-state" / "active-campaign.txt").write_text(
        "test-campaign", encoding="utf-8"
    )
    campaign_dir = project_root / "world-state" / "campaigns" / "test-campaign"
    campaign_dir.mkdir(parents=True, exist_ok=True)

    core_files = [
        campaign_dir / "campaign-overview.json",
        campaign_dir / "npcs.json",
        campaign_dir / "locations.json",
        campaign_dir / "facts.json",
        campaign_dir / "session-log.md",
    ]
    for core_file in core_files:
        core_file.write_text("{}", encoding="utf-8")

    extraction_artifacts = [
        campaign_dir / "chunks",
        campaign_dir / "extracted",
        campaign_dir / "merged-results.json",
        campaign_dir / "metadata.json",
        campaign_dir / "current-document.txt",
    ]
    (campaign_dir / "chunks").mkdir()
    (campaign_dir / "chunks" / "chunk_000.txt").write_text("chunk", encoding="utf-8")
    (campaign_dir / "extracted").mkdir()
    (campaign_dir / "extracted" / "npcs.json").write_text("{}", encoding="utf-8")
    (campaign_dir / "merged-results.json").write_text("{}", encoding="utf-8")
    (campaign_dir / "metadata.json").write_text("{}", encoding="utf-8")
    (campaign_dir / "current-document.txt").write_text("source", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(extract_script), "clean", "test-campaign"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    assert campaign_dir.is_dir(), "clean must not delete the campaign root directory"

    for core_file in core_files:
        assert core_file.exists(), f"core campaign file was deleted: {core_file.name}"

    for artifact in extraction_artifacts:
        assert not artifact.exists(), f"extraction artifact was not removed: {artifact.name}"
