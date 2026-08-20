from unittest import mock

import arctic_shift_client
import data_source
import reddit_client
from config import settings


def test_default_data_source_dispatches_to_arctic_shift(monkeypatch):
    monkeypatch.setattr(settings, "data_source", "arctic_shift")
    fake = mock.Mock(return_value=[{"id": "1"}])
    monkeypatch.setattr(arctic_shift_client, "fetch_posts", fake)

    result = data_source.fetch_posts()

    fake.assert_called_once()
    assert result == [{"id": "1"}]


def test_praw_data_source_dispatches_to_reddit_client(monkeypatch):
    monkeypatch.setattr(settings, "data_source", "praw")
    fake = mock.Mock(return_value=[{"id": "2"}])
    monkeypatch.setattr(reddit_client, "fetch_posts", fake)

    result = data_source.fetch_posts()

    fake.assert_called_once()
    assert result == [{"id": "2"}]
