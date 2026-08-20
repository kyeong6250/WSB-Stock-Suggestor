"""Path resolution that works both from source and inside a PyInstaller --onefile exe.

Frozen apps have two relevant locations, which are NOT the same directory:
  - the bundle dir (sys._MEIPASS): a temp dir holding read-only resources
    (frontend static files, ticker CSVs) that were packed into the exe. It's
    wiped after the process exits, so nothing user-editable can live here.
  - the app dir (folder containing the .exe itself): stable across runs, so
    this is where user data like .env has to live.
"""

import sys
from pathlib import Path

IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    APP_DIR = Path(sys.executable).parent
else:
    BUNDLE_DIR = Path(__file__).parent.parent
    APP_DIR = BUNDLE_DIR

FRONTEND_DIR = BUNDLE_DIR / "frontend"
DATA_DIR = BUNDLE_DIR / "backend" / "data" if not IS_FROZEN else BUNDLE_DIR / "data"
ENV_FILE = APP_DIR / ".env"
ENV_EXAMPLE_FILE = BUNDLE_DIR / ".env.example"
