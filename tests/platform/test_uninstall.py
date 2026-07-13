import os
import subprocess
from pathlib import Path


def test_uninstall_removes_only_kit_owned_root(tmp_path: Path) -> None:
    home = tmp_path / "home"
    kit = home / ".local/share/ugc-video"
    unrelated = home / ".local/share/unrelated"
    kit.mkdir(parents=True)
    unrelated.mkdir(parents=True)
    env = {**os.environ, "HOME": str(home), "UGC_VIDEO_HOME": str(kit)}
    subprocess.run(["bash", "scripts/uninstall.sh", "--yes"], check=True, env=env)
    assert not kit.exists()
    assert unrelated.exists()
