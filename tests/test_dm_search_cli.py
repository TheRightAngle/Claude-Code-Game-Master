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
