import sys
import types
from unittest import mock

# desktop.py imports pywebview, whose GUI backend (GTK/Qt on Linux) may not
# be installed in a headless CI runner. These tests only exercise the
# .env-setup logic, not webview itself, so stub it out before importing.
if "webview" not in sys.modules:
    sys.modules["webview"] = types.ModuleType("webview")

import desktop
from config import settings


def test_default_data_source_needs_no_prompt(monkeypatch):
    monkeypatch.setattr(settings, "data_source", "arctic_shift")
    monkeypatch.setattr(settings, "reddit_client_id", "")

    with mock.patch("tkinter.simpledialog.askstring") as ask_string:
        desktop._prompt_for_praw_client_id_if_needed()

    ask_string.assert_not_called()


def test_praw_with_existing_client_id_needs_no_prompt(monkeypatch):
    monkeypatch.setattr(settings, "data_source", "praw")
    monkeypatch.setattr(settings, "reddit_client_id", "already-set")

    with mock.patch("tkinter.simpledialog.askstring") as ask_string:
        desktop._prompt_for_praw_client_id_if_needed()

    ask_string.assert_not_called()


def test_praw_without_client_id_prompts_and_saves(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    monkeypatch.setattr(desktop, "ENV_FILE", env_file)
    monkeypatch.setattr(settings, "data_source", "praw")
    monkeypatch.setattr(settings, "reddit_client_id", "")

    with (
        mock.patch("tkinter.Tk"),
        mock.patch("tkinter.messagebox.showinfo"),
        mock.patch("tkinter.simpledialog.askstring", return_value=" abc123 "),
        mock.patch("webbrowser.open") as browser_open,
    ):
        desktop._prompt_for_praw_client_id_if_needed()

    browser_open.assert_called_once_with("https://www.reddit.com/prefs/apps")
    assert settings.reddit_client_id == "abc123"
    assert env_file.read_text(encoding="utf-8") == "DATA_SOURCE=praw\nREDDIT_CLIENT_ID=abc123\n"


def test_praw_prompt_cancelled_does_not_write_env(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    monkeypatch.setattr(desktop, "ENV_FILE", env_file)
    monkeypatch.setattr(settings, "data_source", "praw")
    monkeypatch.setattr(settings, "reddit_client_id", "")

    with (
        mock.patch("tkinter.Tk"),
        mock.patch("tkinter.messagebox.showinfo"),
        mock.patch("tkinter.simpledialog.askstring", return_value=None),
        mock.patch("webbrowser.open"),
    ):
        desktop._prompt_for_praw_client_id_if_needed()

    assert not env_file.exists()


def test_write_client_id_updates_existing_line(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("DATA_SOURCE=praw\nREDDIT_CLIENT_ID=old\nSUBREDDIT=wallstreetbets\n", encoding="utf-8")
    monkeypatch.setattr(desktop, "ENV_FILE", env_file)

    desktop._write_client_id_to_env("new")

    assert env_file.read_text(encoding="utf-8") == "DATA_SOURCE=praw\nREDDIT_CLIENT_ID=new\nSUBREDDIT=wallstreetbets\n"
