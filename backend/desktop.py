"""Desktop entry point: runs the FastAPI app in a background thread and shows
it inside a native window via pywebview, instead of a browser tab.
"""

import sys
import threading
import time
import tkinter
import webbrowser
from tkinter import messagebox, simpledialog

import uvicorn
import webview

from runtime_paths import ENV_EXAMPLE_FILE, ENV_FILE

HOST = "127.0.0.1"
PORT = 8765


def _write_env_with_client_id(client_id: str) -> None:
    template = ENV_EXAMPLE_FILE.read_text(encoding="utf-8") if ENV_EXAMPLE_FILE.exists() else "REDDIT_CLIENT_ID=\n"
    content = template.replace("REDDIT_CLIENT_ID=\n", f"REDDIT_CLIENT_ID={client_id}\n", 1)
    ENV_FILE.write_text(content, encoding="utf-8")


def _has_client_id() -> bool:
    if not ENV_FILE.exists():
        return False
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("REDDIT_CLIENT_ID=") and line.split("=", 1)[1].strip():
            return True
    return False


def _ensure_env_file() -> bool:
    """Returns True if the app should keep starting, False if it should exit
    because the user didn't complete the one-time Reddit setup prompt."""
    if _has_client_id():
        return True

    root = tkinter.Tk()
    root.withdraw()

    messagebox.showinfo(
        "WSB Stock Suggestor — first-time setup",
        "This app needs a free Reddit API client ID to fetch posts (no password, "
        "no secret to copy).\n\n"
        "A Reddit page is about to open:\n"
        "1. Log in, click 'create app' (bottom of page)\n"
        "2. Choose type 'installed app'\n"
        "3. Name it anything; for 'redirect uri' put http://localhost:8080\n"
        "4. Click 'create app', then copy the string shown under the app's name "
        "(that's the client ID — there's no secret to copy for this type)\n\n"
        "Click OK, then paste that client ID into the box that follows.",
    )
    webbrowser.open("https://www.reddit.com/prefs/apps")

    client_id = simpledialog.askstring(
        "WSB Stock Suggestor — paste client ID",
        "Reddit client ID:",
        parent=root,
    )
    root.destroy()

    if not client_id or not client_id.strip():
        messagebox.showinfo(
            "WSB Stock Suggestor",
            "No client ID entered — closing. Just relaunch the app whenever you're ready to finish setup.",
        )
        return False

    _write_env_with_client_id(client_id.strip())
    return True


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
        background_color="#f4f4f3",
    )
    webview.start()


if __name__ == "__main__":
    main()
