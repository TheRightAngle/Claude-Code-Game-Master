import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _prepare_isolated_enhance_cli(tmp_path: Path) -> tuple[Path, Path]:
    project_root = tmp_path / "project"
    tools_dir = project_root / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(REPO_ROOT / "tools" / "dm-enhance.sh", tools_dir / "dm-enhance.sh")
    shutil.copy2(REPO_ROOT / "tools" / "common.sh", tools_dir / "common.sh")

    return project_root, tools_dir / "dm-enhance.sh"


def test_dm_enhance_fails_cleanly_without_active_campaign(tmp_path: Path) -> None:
    project_root, enhance_script = _prepare_isolated_enhance_cli(tmp_path)
    lib_dir = project_root / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)
    (lib_dir / "entity_enhancer.py").write_text(
        'raise RuntimeError("No active campaign. Run /new-game or /import first.")\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", str(enhance_script), "find", "Grimjaw"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=1,
    )

    combined_output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode != 0
    assert "No active campaign. Run /new-game or /import first." in result.stderr
    assert "Traceback" not in combined_output
