from unittest import mock

import pytest
import requests

import arctic_shift_client as asc
from errors import RedditFetchError


def _fake_response(json_data, status_ok=True, status_code=422):
    resp = mock.Mock()
    resp.json.return_value = json_data
    if status_ok:
        resp.raise_for_status.return_value = None
    else:
        error = requests.HTTPError("boom")
        error.response = mock.Mock(status_code=status_code)
        resp.raise_for_status.side_effect = error
    return resp


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    monkeypatch.setattr(asc.time, "sleep", lambda seconds: None)


def test_looks_stickied_for_moderator_distinguished():
    assert asc._looks_stickied({"distinguished": "moderator", "title": "whatever"}) is True


def test_looks_stickied_for_megathread_title():
    assert asc._looks_stickied({"title": "Daily Discussion Thread for August 20, 2026"}) is True


def test_looks_stickied_false_for_normal_post():
    assert asc._looks_stickied({"title": "GME to the moon", "distinguished": None}) is False


def test_get_retries_then_raises_after_exhausting_attempts(monkeypatch):
    get_mock = mock.Mock(side_effect=requests.ConnectionError("no route"))
    monkeypatch.setattr(requests, "get", get_mock)

    with pytest.raises(RedditFetchError, match="Failed to reach Arctic Shift"):
        asc._get("/api/posts/search", {})

    assert get_mock.call_count == asc.MAX_ATTEMPTS


def test_get_does_not_retry_non_retryable_status(monkeypatch):
    get_mock = mock.Mock(return_value=_fake_response({}, status_ok=False, status_code=404))
    monkeypatch.setattr(requests, "get", get_mock)

    with pytest.raises(RedditFetchError):
        asc._get("/api/posts/search", {})

    assert get_mock.call_count == 1


def test_get_retries_retryable_status_then_succeeds(monkeypatch):
    bad_response = _fake_response({}, status_ok=False, status_code=422)
    good_response = _fake_response({"data": [{"id": "abc"}]})
    get_mock = mock.Mock(side_effect=[bad_response, good_response])
    monkeypatch.setattr(requests, "get", get_mock)

    result = asc._get("/api/posts/search", {})

    assert result == [{"id": "abc"}]
    assert get_mock.call_count == 2


def test_get_returns_data_list(monkeypatch):
    monkeypatch.setattr(requests, "get", mock.Mock(return_value=_fake_response({"data": [{"id": "abc"}]})))
    assert asc._get("/api/posts/search", {}) == [{"id": "abc"}]


def test_fetch_posts_filters_stickied_and_shapes_output(monkeypatch):
    posts_response = _fake_response(
        {
            "data": [
                {
                    "id": "abc123",
                    "title": "GME to the moon",
                    "selftext": "diamond hands",
                    "score": 500,
                    "num_comments": 10,
                    "link_flair_text": "DD",
                    "created_utc": 1700000000,
                    "distinguished": None,
                },
                {
                    "id": "megathread1",
                    "title": "Daily Discussion Thread for August 20, 2026",
                    "selftext": "",
                    "score": 5,
                    "num_comments": 900,
                    "link_flair_text": None,
                    "created_utc": 1700000001,
                    "distinguished": "moderator",
                },
            ]
        }
    )
    comments_response = _fake_response({"data": []})

    def fake_get(url, params, timeout, headers):
        if "posts/search" in url:
            return posts_response
        return comments_response

    monkeypatch.setattr(requests, "get", mock.Mock(side_effect=fake_get))
    monkeypatch.setattr(asc.time, "sleep", lambda seconds: None)

    posts = asc.fetch_posts()

    assert len(posts) == 1
    post = posts[0]
    assert post["id"] == "abc123"
    assert post["flair"] == "DD"
    assert post["score"] == 500
    assert post["permalink"] == "https://reddit.com/r/wallstreetbets/comments/abc123/"
    assert "GME to the moon" in post["text_blobs"][0]


def test_fetch_posts_skips_comment_request_when_num_comments_is_zero(monkeypatch):
    posts_response = _fake_response(
        {
            "data": [
                {
                    "id": "nocomments1",
                    "title": "quiet post",
                    "selftext": "",
                    "score": 3,
                    "num_comments": 0,
                    "link_flair_text": "Discussion",
                    "created_utc": 1700000000,
                    "distinguished": None,
                }
            ]
        }
    )
    get_mock = mock.Mock(return_value=posts_response)
    monkeypatch.setattr(requests, "get", get_mock)
    sleep_mock = mock.Mock()
    monkeypatch.setattr(asc.time, "sleep", sleep_mock)

    posts = asc.fetch_posts()

    assert len(posts) == 1
    assert get_mock.call_count == 1  # only the posts/search call, no comment fetch
    sleep_mock.assert_not_called()


def _post(post_id, score, num_comments=5):
    return {
        "id": post_id,
        "title": f"post {post_id}",
        "selftext": "",
        "score": score,
        "num_comments": num_comments,
        "link_flair_text": "Discussion",
        "created_utc": 1700000000,
        "distinguished": None,
    }


def test_comment_fetching_is_capped_to_highest_scoring_posts(monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "arctic_shift_max_comment_fetches", 2)

    posts_data = [_post("low", score=1), _post("high", score=100), _post("mid", score=50)]
    posts_response = _fake_response({"data": posts_data})
    comments_response = _fake_response({"data": []})
    requested_link_ids = []

    def fake_get(url, params, timeout, headers):
        if "posts/search" in url:
            return posts_response
        requested_link_ids.append(params["link_id"])
        return comments_response

    monkeypatch.setattr(requests, "get", mock.Mock(side_effect=fake_get))

    asc.fetch_posts()

    # Only the top 2 by score should have triggered a comment fetch.
    assert set(requested_link_ids) == {"t3_high", "t3_mid"}


def test_fetch_top_comments_ranks_by_score_and_caps_at_limit(monkeypatch):
    comments_response = _fake_response(
        {
            "data": [
                {"id": "c1", "body": "low score", "score": 1},
                {"id": "c2", "body": "high score", "score": 50},
                {"id": "c3", "body": "mid score", "score": 10},
            ]
        }
    )
    get_mock = mock.Mock(return_value=comments_response)
    monkeypatch.setattr(requests, "get", get_mock)

    top = asc._fetch_top_comments("abc123", limit=2)

    assert top == ["high score", "mid score"]
    # link_id must be a Reddit fullname (t3_ prefix) — a bare post id times
    # out server-side instead of erroring, so this is easy to silently break.
    assert get_mock.call_args.kwargs["params"]["link_id"] == "t3_abc123"


def test_fetch_top_comments_returns_empty_for_zero_limit(monkeypatch):
    get_mock = mock.Mock()
    monkeypatch.setattr(requests, "get", get_mock)

    assert asc._fetch_top_comments("abc123", limit=0) == []
    get_mock.assert_not_called()
