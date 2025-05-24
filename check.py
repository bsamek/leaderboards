import requests
import re
import argparse
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
TIMEOUT = 10  # seconds for requests

# Build regex patterns
patterns = {
    'claude_4_sonnet': re.compile(r'claude[- ]?4[- ]?sonnet', re.IGNORECASE),
    'claude_4_opus': re.compile(r'claude[- ]?4[- ]?opus', re.IGNORECASE),
    'claude_sonnet_4': re.compile(r'claude[- ]?sonnet[- ]?4', re.IGNORECASE),
    'claude_opus_4': re.compile(r'claude[- ]?opus[- ]?4', re.IGNORECASE),
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
    parser = argparse.ArgumentParser(description='Check leaderboard URLs for model mentions.')
    parser.add_argument('bookmarks_file', help='Path to the HTML bookmarks file')
    args = parser.parse_args()
    
    urls = load_leaderboard_urls(args.bookmarks_file)
    for url in urls:
        res = check_url_for_models(url)
        if 'error' in res:
            print(f"[ERROR] {url} → {res['error']}")
        else:
            found = [name for name, ok in res.items() if ok]
            print(f"{url}\n    → found: {', '.join(found) or 'none'}\n")

if __name__ == '__main__':
    main()
