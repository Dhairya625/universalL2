from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
OUTPUTS = ROOT / "outputs"
VERSION = "0.2.0"


def main() -> int:
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "Automate.spec"], cwd=ROOT, check=True)
    OUTPUTS.mkdir(exist_ok=True)
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Darwin":
        app = DIST / "Automate.app"
        subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(app)], check=True)
        dmg = OUTPUTS / f"Automate-{VERSION}-macOS-{machine}.dmg"
        subprocess.run(["hdiutil", "create", "-volname", "Automate", "-srcfolder", str(app), "-ov", "-format", "UDZO", str(dmg)], check=True)
        print(dmg)
    elif system == "Windows":
        archive = shutil.make_archive(str(OUTPUTS / f"Automate-{VERSION}-Windows-x64"), "zip", DIST, "Automate")
        print(archive)
    elif system == "Linux":
        archive = shutil.make_archive(str(OUTPUTS / f"Automate-{VERSION}-Linux-x64"), "gztar", DIST, "Automate")
        print(archive)
    else:
        raise SystemExit(f"Unsupported build system: {system}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
