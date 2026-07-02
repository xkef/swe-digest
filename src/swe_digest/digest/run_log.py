"""Write the machine-readable run log for one digest day.

Produces data/runs/YYYY-MM-DD.yaml from the day's HN fetch
(.cache/hn/, falling back to the committed data/hn/ snapshot), the
published digest, and the watchlist queries. The script owns the
"mechanical" keys (hn, digest, query_yield) and rewrites them
idempotently; everything else in the file, including the agent's
"judgment" subtree and mechanical.backtest, is preserved. Run logs are
the durable evidence store for the weekly improvement routine, since
data/hn/ snapshots are pruned to seven days and .cache/ is gitignored.
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from swe_digest.paths import ROOT, WATCHLIST


def _represent_str(dumper: yaml.SafeDumper, data: str) -> yaml.Node:
    """Emit multiline strings as literal `|` blocks and long single lines as
    folded `>` blocks, so run-log notes read as wrapped prose instead of one
    long quoted line."""
    if "\n" in data:
        style = "|"
    elif len(data) > 80:
        style = ">"
    else:
        style = None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


yaml.add_representer(str, _represent_str, Dumper=yaml.SafeDumper)

CACHE_DIR = ROOT / ".cache" / "hn"
SNAPSHOT_DIR = ROOT / "data" / "hn"
RUNS_DIR = ROOT / "data" / "runs"
DIGESTS = ROOT / "content" / "digests"

STORY_COLLECTIONS = ["front_page", "top_day", "ask_hn", "show_hn"]

LINK = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)")
HN_ITEM = re.compile(r"news\.ycombinator\.com/item\?id=(\d+)")
SECTION = re.compile(r"^##\s+(.+?)\s*$")
STORY = re.compile(r"^###\s+(.+?)\s*$")


def today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def normalize_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    host = parts.netloc.lower().removeprefix("www.")
    return f"{host}{parts.path.rstrip('/')}"


def load_hn(date: str) -> tuple[dict, str] | None:
    for path, source in (
        (CACHE_DIR / f"{date}.json", "cache"),
        (SNAPSHOT_DIR / f"{date}.json", "snapshot"),
    ):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8")), source
    return None


def hn_stories(data: dict) -> dict[int, dict]:
    stories: dict[int, dict] = {}
    for name in STORY_COLLECTIONS:
        for item in data["collections"].get(name, {}).get("items", []):
            stories.setdefault(item["id"], item)
    return stories


def parse_digest(text: str) -> dict:
    front, body = "", text
    if text.startswith("+++"):
        end = text.find("\n+++", 3)
        if end != -1:
            front, body = text[3:end], text[end + 4 :]

    count_match = re.search(r"^\s*source_count\s*=\s*(\d+)", front, re.MULTILINE)
    sections: dict[str, int] = {}
    titles: list[str] = []
    current = ""
    for line in body.splitlines():
        sec = SECTION.match(line)
        if sec:
            current = sec.group(1)
            sections[current] = 0
            continue
        sto = STORY.match(line)
        if sto and current:
            sections[current] += 1
            titles.append(sto.group(1))

    urls = LINK.findall(body)
    return {
        "sections": sections,
        "titles": titles,
        "source_count": int(count_match.group(1)) if count_match else None,
        "hn_ids": sorted({int(m) for m in HN_ITEM.findall(body)}),
        "urls": sorted({normalize_url(u) for u in urls}),
    }


def load_run_log(date: str) -> dict:
    path = RUNS_DIR / f"{date}.yaml"
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {"date": date}
    return {"date": date}


def save_run_log(date: str, record: dict) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / f"{date}.yaml"
    path.write_text(
        yaml.safe_dump(
            record, sort_keys=False, default_flow_style=False, allow_unicode=True, width=80
        ),
        encoding="utf-8",
    )
    return path


def query_yield(hn: dict, digest: dict) -> dict:
    published_ids = set(digest["hn_ids"])
    published_urls = set(digest["urls"])
    out: dict[str, dict] = {}
    queries = hn["collections"].get("queries", {}).get("items", {})
    for query, items in queries.items():
        matched_ids = sorted({item["id"] for item in items})
        published = sorted(
            item["id"]
            for item in items
            if item["id"] in published_ids
            or (item.get("url") and normalize_url(item["url"]) in published_urls)
        )
        out[query] = {
            "matched": len(matched_ids),
            "matched_ids": matched_ids,
            "published": len(published),
            "published_ids": published,
        }
    return out


def main(date: str | None = None) -> int:
    date = date or today()

    digest_path = DIGESTS / date[:7] / date / "index.md"
    if not digest_path.exists():
        print(f"error: no digest at {digest_path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    digest = parse_digest(digest_path.read_text(encoding="utf-8"))

    loaded = load_hn(date)
    if loaded is None:
        print(f"warn: no HN data for {date} in .cache/hn or data/hn", file=sys.stderr)
        hn_record: dict[str, Any] = {"source": None}
        yields: dict = {}
        seen_ids: list[int] = []
    else:
        hn, source = loaded
        collections = hn["collections"]
        hn_record = {
            "source": source,
            "fetched_at": hn.get("fetched_at"),
            "degraded": hn.get("degraded", []),
            "backends": {
                name: collections.get(name, {}).get("backend")
                for name in [*STORY_COLLECTIONS, "comments"]
            },
            "queries_backend": collections.get("queries", {}).get("backend"),
        }
        yields = query_yield(hn, digest)
        seen_ids = sorted(hn_stories(hn))
    hn_record["seen_ids"] = seen_ids

    with open(WATCHLIST, "rb") as handle:
        for query in tomllib.load(handle)["hacker_news"]["queries"]:
            yields.setdefault(query, None)

    record = load_run_log(date)
    mechanical = record.setdefault("mechanical", {})
    mechanical["generated_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    mechanical["hn"] = hn_record
    mechanical["digest"] = {
        "sections": digest["sections"],
        "source_count": digest["source_count"],
        "hn_ids": digest["hn_ids"],
        "domains": sorted({u.split("/")[0] for u in digest["urls"]}),
    }
    mechanical["query_yield"] = yields

    path = save_run_log(date, record)
    stories = sum(digest["sections"].values())
    matched = sum(1 for y in yields.values() if y and y["matched"])
    print(
        f"run-log {date}: {stories} stories, {len(digest['hn_ids'])} HN links, "
        f"{len(seen_ids)} seen ids ({hn_record['source'] or 'no hn data'}), "
        f"{matched}/{len(yields)} queries with matches"
    )
    print(f"wrote {path.relative_to(ROOT)}")
    return 0
