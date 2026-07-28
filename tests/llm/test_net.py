"""The fetch proxy's text extraction."""

from swe_digest.llm import net


class TestReadable:
    """A page reaches the model as text, not as markup.

    The fetch bound is the whole of what a step gets to read, and on a modern
    page the first twenty thousand characters are stylesheets and scripts. The
    2026-07-28 digest dropped six candidates because their pages "returned head,
    meta, and inline CSS only".
    """

    PAGE = """<!doctype html><html><head>
      <title>Vendor &amp; Co ships a thing</title>
      <style>.a{color:red}</style>
      <script>var tracking = "noise";</script>
      <script type="application/ld+json">{"datePublished": "2026-07-27"}</script>
    </head><body>
      <nav><a href="/x">Home</a></nav>
      <article><h1>Vendor ships a thing</h1><p>The first claim.</p>
      <p>The second claim.</p></article>
    </body></html>"""

    def test_markup_and_script_bodies_are_gone(self) -> None:
        text = net.readable(self.PAGE)

        assert "color:red" not in text
        assert "var tracking" not in text
        assert "<p>" not in text
        assert "The first claim." in text
        assert "The second claim." in text

    def test_the_title_and_json_ld_survive(self) -> None:
        """A citation needs a date, and on most news sites that is only in the
        JSON-LD block a tag-stripper would throw away with the scripts."""
        text = net.readable(self.PAGE)

        assert text.startswith("Vendor & Co ships a thing")
        assert '"datePublished": "2026-07-27"' in text

    def test_the_article_is_reachable_inside_a_realistic_bound(self) -> None:
        bloated = self.PAGE.replace(
            "<style>.a{color:red}</style>", "<style>" + "x{y:z}" * 8000 + "</style>"
        )

        assert len(bloated) > net.MAX_TEXT_CHARS
        assert len(net.readable(bloated)) < net.MAX_TEXT_CHARS

    def test_non_html_is_passed_through(self) -> None:
        """api.github.com is the reliable path for a GitHub fact, and its JSON
        must not be mangled by a markup stripper."""
        payload = '{"tag_name": "v1.2.3", "body": "<b>bold</b> in a release note"}'

        assert net.readable(payload) == payload
