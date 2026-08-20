import pytest

import reddit_client
from config import settings
from reddit_client import RedditFetchError


def test_missing_client_id_raises(monkeypatch):
    monkeypatch.setattr(settings, "reddit_client_id", "")
    with pytest.raises(RedditFetchError, match="REDDIT_CLIENT_ID"):
        reddit_client._make_reddit()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("hot", ["hot"]),
        ("hot,rising", ["hot", "rising"]),
        (" Hot , Rising ", ["hot", "rising"]),
        ("bogus", ["hot"]),
        ("", ["hot"]),
        ("top,bogus,new", ["top", "new"]),
    ],
)
def test_parse_listings(raw, expected):
    assert reddit_client._parse_listings(raw) == expected
