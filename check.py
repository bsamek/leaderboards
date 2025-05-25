import requests
import re
import argparse
import json
import os
from datetime import datetime, UTC
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
TIMEOUT = 10  # seconds for requests
STATE_FILE = "leaderboard_state.json"

# --- Pattern builder helper ---
def build_pattern(model_name: str) -> re.Pattern:
    parts = re.split(r"[ -]+", model_name.strip())
    escaped = [re.escape(p) for p in parts]
    regex = r"[- ]?".join(escaped)          # optional dash/space between each word
    return re.compile(regex, re.IGNORECASE)


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


def check_url_for_models_static(url: str, patterns: dict[str, re.Pattern]):
    """Fetch a URL using requests (static content only)."""
    try:
        r = requests.get(url, timeout=TIMEOUT)
        text = r.text
    except Exception as e:
        return {"error": str(e)}

    found_models = []
    for model_name, pattern in patterns.items():
        if pattern.search(text):
            found_models.append(model_name)
    return {"found": found_models}


def check_url_for_models_dynamic(url: str, patterns: dict[str, re.Pattern]):
    """Fetch a URL using Playwright (handles dynamic content)."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate and wait for content to load
            page.goto(url, timeout=TIMEOUT * 1000)  # Playwright uses milliseconds
            
            # Wait for network to be idle (no requests for 500ms)
            page.wait_for_load_state("networkidle")
            
            # Get the full page content
            text = page.content()
            browser.close()
            
    except Exception as e:
        return {"error": str(e)}

    found_models = []
    for model_name, pattern in patterns.items():
        if pattern.search(text):
            found_models.append(model_name)
    return {"found": found_models}


def check_url_for_models(url: str, patterns: dict[str, re.Pattern], use_dynamic=False):
    """Check URL for models, with option to use dynamic loading."""
    if use_dynamic:
        return check_url_for_models_dynamic(url, patterns)
    
    # Try static first
    result = check_url_for_models_static(url, patterns)
    
    # If static failed or found no models, try dynamic
    if "error" in result or not result["found"]:
        print(f"    → Trying dynamic loading for {url}")
        return check_url_for_models_dynamic(url, patterns)
    
    return result


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
    parser.add_argument(
        "-m", "--model",
        action="append",
        required=True,
        help="Model name to search for (can be repeated)"
    )
    parser.add_argument(
        "--dynamic",
        action="store_true",
        help="Force use of dynamic loading (Playwright) for all URLs"
    )
    args = parser.parse_args()

    # Load previous state
    old_state = load_state(STATE_FILE)
    old_results = old_state.get("results", {}) if old_state else {}

    # Build model patterns from CLI
    cli_models = args.model                          # list[str]
    model_patterns = {m: build_pattern(m) for m in cli_models}

    # Get current scan
    urls = load_leaderboard_urls(args.bookmarks_file)
    current_scan = {}

    for url in urls:
        res = check_url_for_models(url, model_patterns, use_dynamic=args.dynamic)
        if "error" in res:
            print(f"[ERROR] {url} → {res['error']}")
            current_scan[url] = []  # Store empty list for failed URLs
        else:
            found = res["found"]
            current_scan[url] = found
            print(f"{url}\n    → found: {', '.join(found) or 'none'}\n")

    # Merge new scan into accumulated results, removing only rescanned models
    merged_results = old_results.copy()
    rescanned = set(cli_models)

    for url, found_now in current_scan.items():
        prev = set(merged_results.get(url, []))
        prev -= rescanned                 # drop any models we just rescanned
        merged_results[url] = sorted(prev | set(found_now))

    # Compare with previous state and show changes
    changes = compare_states(old_state, merged_results)
    print_changes(changes)

    # Save current state
    save_state(STATE_FILE, merged_results)


if __name__ == "__main__":
    main()
