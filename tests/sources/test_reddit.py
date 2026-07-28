"""Reddit feed parsing, listing selection, and subreddit rotation."""

import pytest

from swe_digest.adapters.http import RateLimited
from swe_digest.sources import feeds, reddit
from swe_digest.sources.reddit import fetch_listing, make_post

SUBS = ["programming", "rust", "golang", "AZURE", "kubernetes"]


def reddit_entry(
    post_id: str,
    permalink: str,
    published: str,
    content: str = "",
) -> str:
    return f"""<entry>
      <author><name>/u/alice</name></author>
      <category term="programming" label="r/programming"/>
      <content type="html">{content}</content>
      <id>{post_id}</id>
      <link href="{permalink}" />
      <published>{published}</published>
      <title>A post</title>
    </entry>"""


def reddit_feed(*entries: str) -> str:
    body = "".join(entries)
    return f'<feed xmlns="http://www.w3.org/2005/Atom">{body}</feed>'


class TestRedditPosts:
    PERMALINK = "https://www.reddit.com/r/programming/comments/1/x/"

    def test_link_post_carries_external_url(self) -> None:
        content = (
            "&lt;a href=&quot;https://example.com/post?a=1&amp;amp;b=2&quot;&gt;[link]&lt;/a&gt;"
        )
        feed = feeds.parse(
            reddit_feed(
                reddit_entry("t3_a", self.PERMALINK, "2026-07-07T00:00:00+00:00", content)
            ).encode()
        )
        post = make_post(feed.entries[0])
        assert post is not None
        assert post["url"] == "https://example.com/post?a=1&b=2"
        assert post["permalink"] == self.PERMALINK
        assert post["subreddit"] == "programming"
        assert post["author"] == "/u/alice"

    def test_self_post_falls_back_to_permalink(self) -> None:
        feed = feeds.parse(
            reddit_feed(reddit_entry("t3_b", self.PERMALINK, "2026-07-07T00:00:00+00:00")).encode()
        )
        post = make_post(feed.entries[0])
        assert post is not None
        assert post["url"] == self.PERMALINK

    def test_old_reddit_permalink_normalized(self) -> None:
        old = "https://old.reddit.com/r/programming/comments/1/x/"
        feed = feeds.parse(
            reddit_feed(reddit_entry("t3_c", old, "2026-07-07T00:00:00+00:00")).encode()
        )
        post = make_post(feed.entries[0])
        assert post is not None
        assert post["permalink"] == self.PERMALINK
        assert post["url"] == self.PERMALINK


class TestRedditListing:
    def test_window_filter_keeps_recent_posts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        feed = reddit_feed(
            reddit_entry("t3_new", TestRedditPosts.PERMALINK, "2026-07-07T00:00:00+00:00"),
            reddit_entry("t3_old", TestRedditPosts.PERMALINK, "2026-07-01T00:00:00+00:00"),
        )
        monkeypatch.setattr(feeds, "fetch_bytes", lambda url, **kwargs: feed.encode())
        posts, healthy = fetch_listing(
            "www.reddit.com", ["programming"], "top_day", "2026-07-06T00:00:00+00:00", pause=0
        )
        assert [post["id"] for post in posts] == ["t3_new"]
        assert healthy == 1

    def test_partial_coverage_kept_and_counted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        feed = reddit_feed(
            reddit_entry("t3_a", TestRedditPosts.PERMALINK, "2026-07-07T00:00:00+00:00")
        )

        def fetch(url: str, **kwargs: object) -> bytes:
            if "/r/programming/" in url:
                return feed.encode()
            raise RuntimeError("blocked")

        monkeypatch.setattr(feeds, "fetch_bytes", fetch)
        subs = ["programming", "rust", "golang", "linux"]
        posts, healthy = fetch_listing(
            "www.reddit.com", subs, "hot", "2026-07-06T00:00:00+00:00", pause=0
        )
        assert [post["id"] for post in posts] == ["t3_a"]
        assert healthy == 1

    def test_zero_coverage_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fetch(url: str, **kwargs: object) -> bytes:
            raise RuntimeError("blocked")

        monkeypatch.setattr(feeds, "fetch_bytes", fetch)
        with pytest.raises(RuntimeError, match="no subreddits returned entries"):
            fetch_listing(
                "www.reddit.com", ["programming"], "hot", "2026-07-06T00:00:00+00:00", pause=0
            )


class TestRedditRotation:
    def test_uncovered_subreddits_come_first(self) -> None:
        ordered = reddit.order_subreddits(SUBS, {"programming", "golang"}, offset=0)
        assert ordered[:3] == ["rust", "AZURE", "kubernetes"]
        assert set(ordered[3:]) == {"programming", "golang"}

    def test_coverage_matching_ignores_case(self) -> None:
        # The watchlist carries display casing; feed entries carry their own.
        ordered = reddit.order_subreddits(SUBS, {"azure"}, offset=0)
        assert ordered[-1] == "AZURE"

    def test_rotation_orders_within_each_group(self) -> None:
        covered = {"programming", "golang"}
        first = reddit.order_subreddits(SUBS, covered, offset=0)
        second = reddit.order_subreddits(SUBS, covered, offset=1)
        assert first != second
        assert set(first) == set(second)

    def test_full_coverage_falls_back_to_plain_rotation(self) -> None:
        covered = {name.lower() for name in SUBS}
        ordered = reddit.order_subreddits(SUBS, covered, offset=2)
        assert ordered == SUBS[2:] + SUBS[:2]

    @pytest.mark.parametrize("offset", [0, 1, 3, 4])
    def test_order_is_always_a_permutation(self, offset: int) -> None:
        # The cheapest guard against silently dropping a feed from the list.
        ordered = reddit.order_subreddits(SUBS, {"rust"}, offset=offset)
        assert sorted(ordered) == sorted(SUBS)

    def test_covered_subreddits_reads_every_listing(self) -> None:
        snapshot = {
            "collections": {
                "top_day": {"items": [{"subreddit": "programming"}, {"subreddit": None}]},
                "hot": {"items": [{"subreddit": "AZURE"}]},
            }
        }
        assert reddit.covered_subreddits(snapshot) == {"programming", "azure"}

    def test_covered_subreddits_tolerates_an_empty_snapshot(self) -> None:
        assert reddit.covered_subreddits({}) == set()


class TestRateLimiting:
    """Unauthenticated Reddit closes for a while once it closes.

    A run on 2026-07-28 spent 23 requests per listing being told 429, each one
    after the seven-second inter-request pause, which is over five minutes of a
    run re-learning what the first response said.
    """

    def test_a_run_of_rate_limits_stops_the_listing(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        tried: list[str] = []

        def fetch(url: str, **kwargs: object) -> bytes:
            tried.append(url)
            raise RateLimited(f"rate limited: {url}")

        monkeypatch.setattr(feeds, "fetch_bytes", fetch)

        with pytest.raises(RuntimeError, match="no subreddits returned entries"):
            fetch_listing("www.reddit.com", SUBS, "hot", "2026-07-06T00:00:00+00:00", pause=0)

        assert len(tried) == reddit.RATE_LIMIT_GIVE_UP, "gave up later than the third 429"
        assert "stopping after 3/5" in capsys.readouterr().err

    def test_one_rate_limit_among_healthy_feeds_does_not_stop_it(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A single 429 can be a blip; only a run of them is the limiter."""
        feed = reddit_feed(
            reddit_entry("t3_a", TestRedditPosts.PERMALINK, "2026-07-07T00:00:00+00:00")
        )

        def fetch(url: str, **kwargs: object) -> bytes:
            if "/r/rust/" in url:
                raise RateLimited(f"rate limited: {url}")
            return feed.encode()

        monkeypatch.setattr(feeds, "fetch_bytes", fetch)

        posts, healthy = fetch_listing(
            "www.reddit.com", SUBS, "hot", "2026-07-06T00:00:00+00:00", pause=0
        )

        assert healthy == len(SUBS) - 1
