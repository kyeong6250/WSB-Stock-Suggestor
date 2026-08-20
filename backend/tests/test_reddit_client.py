import pytest

import reddit_client
from config import settings
from reddit_client import RedditFetchError


def test_missing_credentials_raises(monkeypatch):
    monkeypatch.setattr(settings, "reddit_client_id", "")
    monkeypatch.setattr(settings, "reddit_client_secret", "")
    with pytest.raises(RedditFetchError, match="REDDIT_CLIENT_ID"):
        reddit_client._make_reddit()
