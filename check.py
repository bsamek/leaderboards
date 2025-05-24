import requests
import re
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
BOOKMARKS_FILE = 'bookmarks_5_24_25.html'
TIMEOUT = 10  # seconds for requests

# Build regex patterns
patterns = {
    'claude_4': re.compile(r'claude[- ]?4', re.IGNORECASE),
    'opus':     re.compile(r'\bopus\b', re.IGNORECASE),
}

def load_leaderboard_urls(html_path):
    """Parse the bookmarks HTML and return all URLs in the 'Leaderboards' folder."""
    with open(html_path, encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    # Find the <H3> titled "Leaderboards"
    hdr = soup.find('h3', string='Leaderboards')
    if not hdr:
        raise RuntimeError("Could not find 'Leaderboards' folder in bookmarks.")
    dl = hdr.find_next_sibling('dl')
    return [a['href'] for a in dl.find_all('a', href=True)]

def check_url_for_models(url):
    """Fetch a URL and return which patterns were found."""
    try:
        r = requests.get(url, timeout=TIMEOUT)
        text = r.text
    except Exception as e:
        return {'error': str(e)}
    results = {}
    for name, pat in patterns.items():
        results[name] = bool(pat.search(text))
    return results

def main():
    urls = load_leaderboard_urls(BOOKMARKS_FILE)
    for url in urls:
        res = check_url_for_models(url)
        if 'error' in res:
            print(f"[ERROR] {url} → {res['error']}")
        else:
            found = [name for name, ok in res.items() if ok]
            print(f"{url}\n    → found: {', '.join(found) or 'none'}\n")

if __name__ == '__main__':
    main()
