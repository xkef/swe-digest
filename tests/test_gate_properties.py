"""Property-based tests over the gate's pure screening functions.

Hypothesis generates adversarial inputs around the invariants the publish
gate relies on: an unsafe payload embedded in arbitrary prose is always
flagged, entity-encoded payloads cannot slip past the decoder, secret
patterns survive arbitrary surroundings, and the path allowlist never
matches a traversal. Payload templates below are inert test fixtures.
"""

from __future__ import annotations

from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from swe_digest.gate.check_content import (
    scan_secrets,
    scan_unsafe,
    split_front_matter,
    strip_code,
)
from swe_digest.gate.publish_run import ALLOWED_PATHS, domain

PATH = Path("digest.md")

# Prose excludes backticks so generated text cannot open a code span that
# would legitimately swallow the injected payload.
prose = st.text(
    alphabet=st.characters(blacklist_characters="`"),
    max_size=200,
)

UNSAFE_PAYLOADS = [
    "<script>x</script>",
    "<iframe src=x>",
    "<img src=x>",
    "<svg viewBox=x>",
    "<style>x</style>",
    " onload=x",
    "javascript:x",
    "data:text/html,x",
    "data:image/svg+xml,x",
]


class TestScanUnsafe:
    @given(before=prose, after=prose, payload=st.sampled_from(UNSAFE_PAYLOADS))
    def test_payload_in_arbitrary_prose_is_flagged(
        self, before: str, after: str, payload: str
    ) -> None:
        text = f"{before}\n{payload}\n{after}"
        assert scan_unsafe(PATH, text)

    @given(
        before=prose,
        after=prose,
        payload=st.sampled_from(["javascript:x", "<script>x</script>"]),
        encode=st.lists(st.booleans(), min_size=32, max_size=32),
    )
    def test_entity_encoded_payload_is_flagged(
        self, before: str, after: str, payload: str, encode: list[bool]
    ) -> None:
        encoded = "".join(
            f"&#{ord(ch)};" if flag else ch for ch, flag in zip(payload, encode, strict=False)
        )
        text = f"{before}\n{encoded}\n{after}"
        assert scan_unsafe(PATH, text)

    def test_backtick_wrapped_payload_is_allowed(self) -> None:
        assert not scan_unsafe(PATH, "the story mentions `<script>` in backticks")


class TestScanSecrets:
    @given(
        before=st.text(max_size=200),
        after=st.text(max_size=200),
        token=st.one_of(
            st.text(alphabet="abcdefABCDEF0123456789", min_size=20, max_size=40).map(
                lambda s: f"ghp_{s}"
            ),
            st.text(alphabet="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=16, max_size=16).map(
                lambda s: f"AKIA{s}"
            ),
        ),
    )
    def test_secret_in_arbitrary_text_is_flagged(self, before: str, after: str, token: str) -> None:
        assert scan_secrets(PATH, f"{before} {token} {after}")


class TestStripCode:
    @given(text=st.text(max_size=300))
    def test_idempotent(self, text: str) -> None:
        once = strip_code(text)
        assert strip_code(once) == once


class TestSplitFrontMatter:
    @given(
        front=st.text(
            alphabet=st.characters(blacklist_characters="+"),
            max_size=200,
        ),
        body=st.text(max_size=200),
    )
    def test_round_trip(self, front: str, body: str) -> None:
        assert split_front_matter(f"+++{front}\n+++{body}") == (front, body)

    @given(text=st.text(max_size=200))
    def test_missing_marker_returns_none(self, text: str) -> None:
        if not text.startswith("+++"):
            assert split_front_matter(text) is None


class TestDomain:
    @given(
        host=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-",
            min_size=1,
            max_size=50,
        ),
        path=st.text(max_size=50),
        scheme=st.sampled_from(["http", "https"]),
    )
    def test_extracts_lowercased_host(self, host: str, path: str, scheme: str) -> None:
        assert domain(f"{scheme}://{host}/{path}") == host.lower()


class TestAllowedPaths:
    @given(prefix=st.text(max_size=40), suffix=st.text(max_size=40))
    def test_traversal_never_matches(self, prefix: str, suffix: str) -> None:
        candidate = f"{prefix}../{suffix}"
        assert not any(pattern.match(candidate) for pattern in ALLOWED_PATHS)
