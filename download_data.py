"""
Download all raw data for the Virginia Reality Check capstone.

Run once (with internet) from the project folder:
    py download_data.py

Saves everything into raw/ with today's date in each file name.
The notebook reads these saved files and never calls the sources itself.
"""
import json
from datetime import date
from pathlib import Path

import requests

TODAY = date.today().isoformat()          # e.g. 2026-11-21
RAW = Path("raw")
RAW.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

TORVIK_URL = "https://barttorvik.com/2027_team_results.csv"
SCHEDULE_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/"
    "mens-college-basketball/teams/258/schedule"
)
SUMMARY_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/"
    "mens-college-basketball/summary?event={game_id}"
)


def get(url):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response


# 1. Torvik ratings CSV
torvik = get(TORVIK_URL)
torvik_path = RAW / f"torvik_2027_team_results_{TODAY}.csv"
torvik_path.write_bytes(torvik.content)
first_line = torvik.text.splitlines()[0] if torvik.text else ""
print(f"Saved {torvik_path}  ({len(torvik.text.splitlines())} lines)")
print(f"   first line: {first_line[:100]}")
if first_line.lstrip().startswith("<"):
    print("   WARNING: this looks like a web page, not a CSV. Tell Claude.")

# 2. ESPN schedule JSON
schedule = get(SCHEDULE_URL).json()
schedule_path = RAW / f"espn_schedule_{TODAY}.json"
schedule_path.write_text(json.dumps(schedule, indent=2), encoding="utf-8")
events = schedule.get("events", [])
print(f"Saved {schedule_path}  ({len(events)} games on the schedule)")

# 3. One ESPN summary per finished game
finished = [
    e for e in events
    if e["competitions"][0]["status"]["type"]["completed"]
]
print(f"Finished games: {len(finished)}")
for event in finished:
    game_id = event["id"]
    summary = get(SUMMARY_URL.format(game_id=game_id)).json()
    path = RAW / f"espn_summary_{game_id}_{TODAY}.json"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"   Saved {path}  ({event.get('shortName', '')})")

print("\nDone. Pull date:", TODAY)
