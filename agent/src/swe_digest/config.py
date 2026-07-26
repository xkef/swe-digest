"""Central configuration, loaded once from agent/config/config.toml.

The TOML file drives behavior; this module maps it to typed constants so the
rest of the package keeps plain-name imports. agent/config/ sits outside the
unattended publish allowlist and changes only through the owner-approved
improvement-PR path.
"""

import tomllib
from typing import Any

from swe_digest.paths import CONFIG

with (CONFIG / "config.toml").open("rb") as _handle:
    _raw: dict[str, Any] = tomllib.load(_handle)

# Repository identity
REPO: str = _raw["repo"]["name"]
OWNER: str = _raw["repo"]["owner"]
SITE: str = _raw["repo"]["site"]
BRANCH: str = _raw["repo"]["branch"]

# HTTP (all fetchers)
USER_AGENT: str = _raw["http"]["user_agent"]
HTTP_TIMEOUT: int = _raw["http"]["timeout_seconds"]
HTTP_RETRIES: int = _raw["http"]["retries"]
HTTP_MAX_BYTES: int = _raw["http"]["max_response_bytes"]

# Hacker News fetcher
HN_WINDOW_SECONDS: int = _raw["hn"]["window_hours"] * 3600
HN_SNAPSHOT_MAX_AGE_HOURS: int = _raw["hn"]["snapshot_max_age_hours"]
HN_POOL_MAX_ITEMS: int = _raw["hn"]["pool_max_items"]
HN_SNAPSHOT_MAX_ITEMS: int = _raw["hn"]["snapshot_max_items"]
HN_QUERY_CORPUS_NEW_IDS: int = _raw["hn"]["query_corpus_new_ids"]
HN_COMMENT_STORIES: int = _raw["hn"]["comment_stories"]
HN_COMMENTS_PER_STORY: int = _raw["hn"]["comments_per_story"]
HN_COMMENT_MAX_CHARS: int = _raw["hn"]["comment_max_chars"]

# YouTube fetcher
YT_WINDOW_SECONDS: int = _raw["youtube"]["window_hours"] * 3600
YT_SNAPSHOT_MAX_AGE_HOURS: int = _raw["youtube"]["snapshot_max_age_hours"]
YT_DESCRIPTION_MAX_CHARS: int = _raw["youtube"]["description_max_chars"]
YT_DISCUSSION_LOOKUPS: int = _raw["youtube"]["discussion_lookups"]
YT_SNAPSHOT_MAX_ITEMS: int = _raw["youtube"]["snapshot_max_items"]

# Reddit fetcher
REDDIT_WINDOW_SECONDS: int = _raw["reddit"]["window_hours"] * 3600
REDDIT_SNAPSHOT_MAX_AGE_HOURS: int = _raw["reddit"]["snapshot_max_age_hours"]
REDDIT_POOL_MAX_ITEMS: int = _raw["reddit"]["pool_max_items"]
REDDIT_SNAPSHOT_MAX_ITEMS: int = _raw["reddit"]["snapshot_max_items"]
REDDIT_REQUEST_PAUSE_SECONDS: float = _raw["reddit"]["request_pause_seconds"]
REDDIT_MIN_SUBREDDIT_FRACTION: float = _raw["reddit"]["min_subreddit_fraction"]
REDDIT_MIN_DAY_COVERAGE_FRACTION: float = _raw["reddit"]["min_day_coverage_fraction"]

# arXiv papers fetcher
PAPERS_HTTP_TIMEOUT: int = _raw["papers"]["http_timeout_seconds"]
PAPERS_API_PAUSE: int = _raw["papers"]["api_pause_seconds"]
PAPERS_WINDOW_SECONDS: int = _raw["papers"]["window_hours"] * 3600
PAPERS_SNAPSHOT_MAX_AGE_HOURS: int = _raw["papers"]["snapshot_max_age_hours"]
PAPERS_SUMMARY_MAX_CHARS: int = _raw["papers"]["summary_max_chars"]
PAPERS_SNAPSHOT_MAX_ITEMS: int = _raw["papers"]["snapshot_max_items"]

# Book feeds fetcher
BOOKS_WINDOW_SECONDS: int = _raw["books"]["window_days"] * 24 * 3600
BOOKS_SNAPSHOT_MAX_AGE_HOURS: int = _raw["books"]["snapshot_max_age_hours"]
BOOKS_DESCRIPTION_MAX_CHARS: int = _raw["books"]["description_max_chars"]
BOOKS_SNAPSHOT_MAX_ITEMS: int = _raw["books"]["snapshot_max_items"]

# GitHub stars fetcher
STARS_WINDOW_SECONDS: int = _raw["stars"]["window_hours"] * 3600
STARS_REQUEST_PAUSE_SECONDS: float = _raw["stars"]["request_pause_seconds"]
STARS_MAX_REPO_LOOKUPS: int = _raw["stars"]["max_repo_lookups"]
STARS_DESCRIPTION_MAX_CHARS: int = _raw["stars"]["description_max_chars"]

# Events
EVENTS_LEAD_DAYS: int = _raw["events"]["lead_days"]
EVENTS_SOON_DAYS: int = _raw["events"]["soon_days"]

# Digest document vocabulary (section order stays in digest.document)
DIGEST_MAX_TOP_STORIES: int = _raw["digest"]["max_top_stories"]
DIGEST_CATEGORIES: list[str] = _raw["digest"]["categories"]
DIGEST_SOURCES_CHECKED: list[str] = _raw["digest"]["sources_checked"]

# Publish gate and Verified commits
PUBLISH_MAX_COMMITS: int = _raw["publish"]["max_commits"]
PUBLISH_COMMENT_MAX_CHARS: int = _raw["publish"]["comment_max_chars"]
PUBLISH_ISSUE_TITLE_MAX_CHARS: int = _raw["publish"]["issue_title_max_chars"]
PUBLISH_ISSUE_BODY_MAX_CHARS: int = _raw["publish"]["issue_body_max_chars"]
COMMIT_RETRIES: int = _raw["publish"]["commit_retries"]

# Backtest
BACKTEST_MIN_POINTS: int = _raw["backtest"]["min_points"]
BACKTEST_MATCHED_MIN_POINTS: int = _raw["backtest"]["matched_min_points"]
BACKTEST_TITLE_RATIO: float = _raw["backtest"]["title_ratio"]

# Weekly stats
WEEKLY_SECTION_EMPTY_STREAK_DAYS: int = _raw["weekly"]["section_empty_streak_days"]
WEEKLY_STATUS_UNRESOLVED_DAYS: int = _raw["weekly"]["status_unresolved_days"]
WEEKLY_RECURRING_MIN_DAYS: int = _raw["weekly"]["recurring_min_days"]

# Memory gate
MEMORY_MAX_FILE_LINES: int = _raw["memory"]["max_file_lines"]
MEMORY_MAX_LINE_CHARS: int = _raw["memory"]["max_line_chars"]
MEMORY_MAX_FILE_BYTES: int = _raw["memory"]["max_file_bytes"]
MEMORY_MAX_OPEN_FOLLOWUPS: int = _raw["memory"]["max_open_followups"]
MEMORY_MAX_DATED_BULLETS: int = _raw["memory"]["max_dated_bullets"]
MEMORY_ENTITY_STALE_DAYS: int = _raw["memory"]["entity_stale_days"]
MEMORY_FOLLOWUP_MAX_AGE_DAYS: int = _raw["memory"]["followup_max_age_days"]
MEMORY_ACCESS_NOTE_STALE_DAYS: int = _raw["memory"]["access_note_stale_days"]
MEMORY_RUN_DETAIL_DAYS: int = _raw["memory"]["run_log_detail_days"]

# Staged pipeline. The tool grant is not here on purpose: this file is
# proposable through the improvement path, so a grant here would let a run
# propose widening its own capability. See swe_digest.agent.specs.
AGENT_MODEL: str = _raw["agent"]["model"]
AGENT_FETCH_MAX_CHARS: int = _raw["agent"]["fetch_max_chars"]
AGENT_TOOL_OUTPUT_MAX_CHARS: int = _raw["agent"]["tool_output_max_chars"]
AGENT_STEPS: dict[str, dict[str, Any]] = _raw["agent"]["steps"]
