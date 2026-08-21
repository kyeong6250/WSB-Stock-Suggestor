from unittest import mock

import pytest

import main
from errors import RedditFetchError


class _StopLoop(Exception):
    """Raised from a mocked time.sleep to break out of the infinite loop."""


def test_background_refresh_loop_calls_get_suggestions_and_sleeps(monkeypatch):
    get_suggestions_mock = mock.Mock()
    sleep_mock = mock.Mock(side_effect=_StopLoop)
    monkeypatch.setattr(main, "get_suggestions", get_suggestions_mock)
    monkeypatch.setattr(main.time, "sleep", sleep_mock)

    with pytest.raises(_StopLoop):
        main._background_refresh_loop()

    get_suggestions_mock.assert_called_once_with(force_refresh=True)
    sleep_mock.assert_called_once_with(main.settings.background_refresh_interval_seconds)


def test_background_refresh_loop_survives_fetch_errors(monkeypatch):
    get_suggestions_mock = mock.Mock(side_effect=RedditFetchError("temporarily down"))
    sleep_mock = mock.Mock(side_effect=_StopLoop)
    monkeypatch.setattr(main, "get_suggestions", get_suggestions_mock)
    monkeypatch.setattr(main.time, "sleep", sleep_mock)

    with pytest.raises(_StopLoop):
        main._background_refresh_loop()

    # The loop must reach time.sleep (and therefore keep looping on the next
    # interval) even when get_suggestions raises — a bad fetch shouldn't kill
    # the background thread permanently.
    get_suggestions_mock.assert_called_once()
    sleep_mock.assert_called_once()
