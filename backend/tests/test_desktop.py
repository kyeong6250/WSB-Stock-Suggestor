import sys
import types
from unittest import mock

# desktop.py imports pywebview, whose GUI backend (GTK/Qt on Linux) may not
# be installed in a headless CI runner. These tests only exercise the
# .env-setup logic, not webview itself, so stub it out before importing.
if "webview" not in sys.modules:
    sys.modules["webview"] = types.ModuleType("webview")

import desktop


def test_first_run_creates_env_file_and_shows_dialog(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    example_file = tmp_path / ".env.example"
    example_file.write_text("REDDIT_CLIENT_ID=\n", encoding="utf-8")

    monkeypatch.setattr(desktop, "ENV_FILE", env_file)
    monkeypatch.setattr(desktop, "ENV_EXAMPLE_FILE", example_file)

    with (
        mock.patch("tkinter.Tk"),
        mock.patch("tkinter.messagebox.showinfo") as show_info,
        mock.patch("os.startfile", create=True),
        mock.patch("webbrowser.open"),
    ):
        should_continue = desktop._ensure_env_file()

    assert should_continue is False
    assert env_file.exists()
    assert env_file.read_text(encoding="utf-8") == "REDDIT_CLIENT_ID=\n"
    show_info.assert_called_once()


def test_second_run_skips_dialog_when_env_already_exists(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("REDDIT_CLIENT_ID=abc\n", encoding="utf-8")

    monkeypatch.setattr(desktop, "ENV_FILE", env_file)

    with mock.patch("tkinter.messagebox.showinfo") as show_info:
        should_continue = desktop._ensure_env_file()

    assert should_continue is True
    show_info.assert_not_called()
