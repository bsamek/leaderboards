import requests
import re
import argparse
import json
import os
from datetime import datetime, UTC
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
TIMEOUT = 10  # seconds for requests
STATE_FILE = "leaderboard_state.json"

# Group patterns by model type

model_patterns = {
    "Claude 4 Sonnet": [
        re.compile(r"claude[- ]?4[- ]?sonnet", re.IGNORECASE),
        re.compile(r"claude[- ]?sonnet[- ]?4", re.IGNORECASE),
    ],
    "Claude 4 Opus": [
        re.compile(r"claude[- ]?4[- ]?opus", re.IGNORECASE),
        re.compile(r"claude[- ]?opus[- ]?4", re.IGNORECASE),
    ],
}


def load_leaderboard_urls(html_path):
    """Parse the bookmarks HTML and return all URLs in the 'Leaderboards' folder."""
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    # Find the <H3> titled "Leaderboards"
    hdr = soup.find("h3", string="Leaderboards")
    if not hdr:
        raise RuntimeError("Could not find 'Leaderboards' folder in bookmarks.")
    dl = hdr.find_next_sibling("dl")
    return [a["href"] for a in dl.find_all("a", href=True)]


def check_url_for_models(url):
    """Fetch a URL and return which model types were found."""
    try:
        r = requests.get(url, timeout=TIMEOUT)
        text = r.text
    except Exception as e:
        return {"error": str(e)}

    found_models = []
    for model_name, patterns in model_patterns.items():
        # Check if any pattern for this model matches
        if any(pattern.search(text) for pattern in patterns):
            found_models.append(model_name)

    return {"found": found_models}


def load_state(filename):
    """Load previous state from JSON file. Returns None if file doesn't exist."""
    if not os.path.exists(filename):
        return None

    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load state file {filename}: {e}")
        return None


def save_state(filename, results):
    """Save current state to JSON file."""
    state = {"last_check": datetime.now(UTC).isoformat(), "results": results}

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Warning: Could not save state file {filename}: {e}")


def compare_states(old_state, new_results):
    """Compare old state with new results and return changes."""
    if old_state is None:
        return {
            "first_run": True,
            "new_urls": list(new_results.keys()),
            "removed_urls": [],
            "model_changes": {},
        }

    old_results = old_state.get("results", {})

    # Find new and removed URLs
    old_urls = set(old_results.keys())
    new_urls = set(new_results.keys())

    changes = {
        "first_run": False,
        "new_urls": list(new_urls - old_urls),
        "removed_urls": list(old_urls - new_urls),
        "model_changes": {},
    }

    # Check for model changes in existing URLs
    for url in old_urls & new_urls:
        old_models = set(old_results[url])
        new_models = set(new_results[url])

        added_models = new_models - old_models
        removed_models = old_models - new_models

        if added_models or removed_models:
            changes["model_changes"][url] = {
                "added": list(added_models),
                "removed": list(removed_models),
            }

    return changes


def print_changes(changes):
    """Print a summary of changes since last run."""
    if changes["first_run"]:
        print("=== FIRST RUN ===")
        print(f"Found {len(changes['new_urls'])} URLs to monitor.\n")
        return

    print("=== CHANGES SINCE LAST RUN ===")

    has_changes = False

    if changes["new_urls"]:
        has_changes = True
        print(f"NEW URLs ({len(changes['new_urls'])}):")
        for url in changes["new_urls"]:
            print(f"  + {url}")
        print()

    if changes["removed_urls"]:
        has_changes = True
        print(f"REMOVED URLs ({len(changes['removed_urls'])}):")
        for url in changes["removed_urls"]:
            print(f"  - {url}")
        print()

    if changes["model_changes"]:
        has_changes = True
        print(f"MODEL CHANGES ({len(changes['model_changes'])} URLs):")
        for url, change in changes["model_changes"].items():
            print(f"  {url}")
            for model in change["added"]:
                print(f"    + {model}")
            for model in change["removed"]:
                print(f"    - {model}")
        print()

    if not has_changes:
        print("No changes detected.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Check leaderboard URLs for model mentions."
    )
    parser.add_argument("bookmarks_file", help="Path to the HTML bookmarks file")
    args = parser.parse_args()

    # Load previous state
    old_state = load_state(STATE_FILE)

    # Get current results
    urls = load_leaderboard_urls(args.bookmarks_file)
    current_results = {}

    for url in urls:
        res = check_url_for_models(url)
        if "error" in res:
            print(f"[ERROR] {url} → {res['error']}")
            current_results[url] = []  # Store empty list for failed URLs
        else:
            found = res["found"]
            current_results[url] = found
            print(f"{url}\n    → found: {', '.join(found) or 'none'}\n")

    # Compare with previous state and show changes
    changes = compare_states(old_state, current_results)
    print_changes(changes)

    # Save current state
    save_state(STATE_FILE, current_results)


if __name__ == "__main__":
    main()
