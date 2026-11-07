from digest import runs

DAILY = {
    "mode": "daily",
    "candidates": 300,
    "added": ["a", "b"],
    "rejected": [{"title": "c", "reason": "Security is full"}],
    "fetched": [{"url": "https://a.dev/", "ok": True}] * 4,
    "usage": {"cost_usd": 1.5, "seconds": 90},
}


UNFINISHED = {"mode": "daily", "started": "2026-11-06T01:30Z"}
WEEKLY = {"mode": "improve", "usage": {"cost_usd": 3.0, "seconds": 60}}
LOGS = [
    {"date": "2026-11-05", "runs": [UNFINISHED]},
    {"date": "2026-11-06", "runs": [DAILY, UNFINISHED]},
    {"date": "2026-11-07", "runs": [DAILY, WEEKLY]},
]


def test_daily_skips_days_without_a_complete_run():
    assert runs.daily(LOGS) == [
        {"date": "2026-11-06", "candidates": 300, "stories": 2, "cost_usd": 1.5},
        {"date": "2026-11-07", "candidates": 300, "stories": 2, "cost_usd": 4.5},
    ]


def test_refusals_counts_each_reason():
    assert runs.refusals(LOGS) == [("Security is full", 2)]


def test_summary_counts_complete_daily_runs_and_every_cost():
    assert runs.summary(LOGS) == {
        "days": 2,
        "runs": 2,
        "candidates": 600,
        "stories": 4,
        "refused": 2,
        "fetches": 8,
        "cost_usd": 6.0,
        "run_seconds": 90,
    }
