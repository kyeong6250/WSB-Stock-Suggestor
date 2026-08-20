import sys
import types
from unittest import mock

# desktop.py imports pywebview, whose GUI backend (GTK/Qt on Linux) may not
# be installed in a headless CI runner. These tests only exercise the
# .env-setup logic, not webview itself, so stub it out before importing.
if "webview" not in sys.modules:
    sys.modules["webview"] = types.ModuleType("webview")

import desktop


def test_first_run_prompts_and_writes_client_id(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    example_file = tmp_path / ".env.example"
    example_file.write_text("REDDIT_CLIENT_ID=\nSUBREDDIT=wallstreetbets\n", encoding="utf-8")

    monkeypatch.setattr(desktop, "ENV_FILE", env_file)
    monkeypatch.setattr(desktop, "ENV_EXAMPLE_FILE", example_file)

    with (
        mock.patch("tkinter.Tk"),
        mock.patch("tkinter.messagebox.showinfo") as show_info,
        mock.patch("tkinter.simpledialog.askstring", return_value=" abc123 ") as ask_string,
        mock.patch("webbrowser.open") as browser_open,
    ):
        should_continue = desktop._ensure_env_file()

    assert should_continue is True
    assert ask_string.called
    browser_open.assert_called_once_with("https://www.reddit.com/prefs/apps")
    show_info.assert_called_once()  # only the intro dialog, no failure dialog
    assert env_file.read_text(encoding="utf-8") == "REDDIT_CLIENT_ID=abc123\nSUBREDDIT=wallstreetbets\n"


def test_first_run_cancelled_prompt_exits_without_writing_env(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    example_file = tmp_path / ".env.example"
    example_file.write_text("REDDIT_CLIENT_ID=\n", encoding="utf-8")

    monkeypatch.setattr(desktop, "ENV_FILE", env_file)
    monkeypatch.setattr(desktop, "ENV_EXAMPLE_FILE", example_file)

    with (
        mock.patch("tkinter.Tk"),
        mock.patch("tkinter.messagebox.showinfo"),
        mock.patch("tkinter.simpledialog.askstring", return_value=None),
        mock.patch("webbrowser.open"),
    ):
        should_continue = desktop._ensure_env_file()

    assert should_continue is False
    assert not env_file.exists()


def test_second_run_skips_prompt_when_client_id_already_set(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("REDDIT_CLIENT_ID=abc123\n", encoding="utf-8")

    monkeypatch.setattr(desktop, "ENV_FILE", env_file)

    with mock.patch("tkinter.simpledialog.askstring") as ask_string:
        should_continue = desktop._ensure_env_file()

    assert should_continue is True
    ask_string.assert_not_called()


def test_has_client_id_false_when_env_value_is_blank(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("REDDIT_CLIENT_ID=\nSUBREDDIT=wallstreetbets\n", encoding="utf-8")

    monkeypatch.setattr(desktop, "ENV_FILE", env_file)

    assert desktop._has_client_id() is False
