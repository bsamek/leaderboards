import requests
import re
import argparse
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
TIMEOUT = 10  # seconds for requests

# Group patterns by model type
model_patterns = {
    'Claude 4 Sonnet': [
        re.compile(r'claude[- ]?4[- ]?sonnet', re.IGNORECASE),
        re.compile(r'claude[- ]?sonnet[- ]?4', re.IGNORECASE)
    ],
    'Claude 4 Opus': [
        re.compile(r'claude[- ]?4[- ]?opus', re.IGNORECASE),
        re.compile(r'claude[- ]?opus[- ]?4', re.IGNORECASE)
    ]
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
    """Fetch a URL and return which model types were found."""
    try:
        r = requests.get(url, timeout=TIMEOUT)
        text = r.text
    except Exception as e:
        return {'error': str(e)}
    
    found_models = []
    for model_name, patterns in model_patterns.items():
        # Check if any pattern for this model matches
        if any(pattern.search(text) for pattern in patterns):
            found_models.append(model_name)
    
    return {'found': found_models}

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
            found = res['found']
            print(f"{url}\n    → found: {', '.join(found) or 'none'}\n")

if __name__ == '__main__':
    main()
