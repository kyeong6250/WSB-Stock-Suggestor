"""Desktop entry point: runs the FastAPI app in a background thread and shows
it inside a native window via pywebview, instead of a browser tab.

With the default DATA_SOURCE=arctic_shift, no setup is needed at all — the
app just opens. The prompt below only fires if someone has opted into
DATA_SOURCE=praw (the official Reddit API) but hasn't set a client ID yet.
"""

import threading
import time
import tkinter
import webbrowser
from tkinter import messagebox, simpledialog

import uvicorn
import webview

from config import settings
from runtime_paths import ENV_FILE

HOST = "127.0.0.1"
PORT = 8765


def _write_client_id_to_env(client_id: str) -> None:
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
        if any(line.strip().startswith("REDDIT_CLIENT_ID=") for line in lines):
            lines = [f"REDDIT_CLIENT_ID={client_id}" if line.strip().startswith("REDDIT_CLIENT_ID=") else line for line in lines]
        else:
            lines.append(f"REDDIT_CLIENT_ID={client_id}")
        content = "\n".join(lines) + "\n"
    else:
        content = f"DATA_SOURCE=praw\nREDDIT_CLIENT_ID={client_id}\n"
    ENV_FILE.write_text(content, encoding="utf-8")


def _prompt_for_praw_client_id_if_needed() -> None:
    """If .env opts into DATA_SOURCE=praw without a client ID, ask for one.
    Never blocks the app from opening either way — if this is skipped or
    cancelled, the dashboard's existing 'missing credential' error explains
    what to do, same as any other misconfiguration.
    """
    if settings.data_source != "praw" or settings.reddit_client_id:
        return

    root = tkinter.Tk()
    root.withdraw()

    messagebox.showinfo(
        "WSB Stock Suggestor — Reddit API setup",
        "DATA_SOURCE=praw is set but no client ID was found.\n\n"
        "A Reddit page is about to open:\n"
        "1. Log in, click 'create app' (bottom of page)\n"
        "2. Choose type 'installed app'\n"
        "3. Name it anything; for 'redirect uri' put http://localhost:8080\n"
        "4. Click 'create app', then copy the string shown under the app's name "
        "(that's the client ID — there's no secret to copy for this type)\n\n"
        "Click OK, then paste that client ID into the box that follows. "
        "(Or just close this — the app will still open using arctic_shift-style "
        "fetching only if you switch DATA_SOURCE back in .env.)",
    )
    webbrowser.open("https://www.reddit.com/prefs/apps")

    client_id = simpledialog.askstring("WSB Stock Suggestor — paste client ID", "Reddit client ID:", parent=root)
    root.destroy()

    if client_id and client_id.strip():
        settings.reddit_client_id = client_id.strip()
        _write_client_id_to_env(client_id.strip())


def _run_server() -> None:
    from main import app

    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


def main() -> None:
    _prompt_for_praw_client_id_if_needed()

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
