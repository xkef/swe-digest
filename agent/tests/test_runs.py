from digest import runs

DAILY = {
    "mode": "daily",
    "candidates": 300,
    "added": ["a", "b"],
    "rejected": [{"title": "c", "reason": "Security is full"}],
    "fetched": [{"url": "https://a.dev/", "ok": True}] * 4,
    "usage": {"cost_usd": 1.5, "seconds": 90},
}


def test_summary_counts_complete_daily_runs_and_every_cost():
    unfinished = {"mode": "daily", "started": "2026-11-06T01:30Z"}
    weekly = {"mode": "improve", "usage": {"cost_usd": 3.0, "seconds": 60}}
    logs = [
        {"date": "2026-11-06", "runs": [DAILY, unfinished]},
        {"date": "2026-11-07", "runs": [DAILY, weekly]},
    ]

    assert runs.summary(logs) == {
        "days": 2,
        "runs": 2,
        "candidates": 600,
        "stories": 4,
        "refused": 2,
        "fetches": 8,
        "cost_usd": 6.0,
        "run_seconds": 90,
    }
