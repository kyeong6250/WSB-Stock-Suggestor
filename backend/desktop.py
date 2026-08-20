"""Desktop entry point: runs the FastAPI app in a background thread and shows
it inside a native window via pywebview, instead of a browser tab.
"""

import sys
import threading
import time
import tkinter
import webbrowser
from tkinter import messagebox

import uvicorn
import webview

from runtime_paths import ENV_EXAMPLE_FILE, ENV_FILE

HOST = "127.0.0.1"
PORT = 8765


def _ensure_env_file() -> bool:
    """Returns True if the app should keep starting, False if it should exit
    so the user can fill in Reddit credentials first."""
    if ENV_FILE.exists():
        return True

    template = ENV_EXAMPLE_FILE.read_text(encoding="utf-8") if ENV_EXAMPLE_FILE.exists() else ""
    ENV_FILE.write_text(template, encoding="utf-8")

    root = tkinter.Tk()
    root.withdraw()
    messagebox.showinfo(
        "WSB Stock Suggestor — first-time setup",
        "This app needs your own free Reddit API credentials to fetch posts.\n\n"
        f"A blank config file was just created at:\n{ENV_FILE}\n\n"
        "1. Get credentials at reddit.com/prefs/apps (choose type 'script')\n"
        "2. Paste them into the file that's about to open\n"
        "3. Save it and re-launch this app\n\n"
        "Click OK to open the config file and the Reddit apps page.",
    )
    root.destroy()

    try:
        import os

        os.startfile(ENV_FILE)  # noqa: S606 - opening a local text file, not executing it
    except Exception:
        pass
    webbrowser.open("https://www.reddit.com/prefs/apps")

    return False


def _run_server() -> None:
    from main import app

    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


def main() -> None:
    if not _ensure_env_file():
        sys.exit(0)

    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()
    time.sleep(1.2)  # give uvicorn a moment to bind before pointing the window at it

    webview.create_window(
        "WSB Stock Suggestor",
        f"http://{HOST}:{PORT}",
        width=1280,
        height=860,
        min_size=(900, 600),
        background_color="#030014",
    )
    webview.start()


if __name__ == "__main__":
    main()
