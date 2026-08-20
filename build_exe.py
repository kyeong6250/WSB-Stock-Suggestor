"""Builds a single-file Windows executable with PyInstaller.

Usage:
    python build_exe.py

Requires the desktop extras: pip install -r requirements-desktop.txt
Output: dist/WSB-Stock-Suggestor.exe
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

ADD_DATA = [
    (ROOT / "frontend", "frontend"),
    (ROOT / "backend" / "data", "data"),
    (ROOT / ".env.example", "."),
]


def main() -> None:
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "WSB-Stock-Suggestor",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--icon",
        str(ROOT / "assets" / "icon.ico"),
        "--paths",
        str(ROOT / "backend"),
        # vaderSentiment loads its lexicon/emoji .txt files, and praw loads
        # its own praw.ini, as package data at import time — PyInstaller's
        # static analysis doesn't follow those. uvicorn picks its event loop
        # / protocol implementation via dynamic imports it can't see either.
        "--collect-data",
        "vaderSentiment",
        "--collect-data",
        "praw",
        "--collect-all",
        "uvicorn",
        str(ROOT / "backend" / "desktop.py"),
    ]
    for src, dest in ADD_DATA:
        args += ["--add-data", f"{src};{dest}"]

    subprocess.run(args, cwd=ROOT, check=True)
    print("\nBuilt: dist/WSB-Stock-Suggestor.exe")


if __name__ == "__main__":
    main()
