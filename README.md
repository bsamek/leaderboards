# Tools for LLM leaderboards

## check.py

A monitoring tool that tracks when AI models appear on leaderboard websites.

### What it does

`check.py` scans a collection of AI leaderboard URLs (exported from your browser bookmarks) and searches for mentions of specific AI models that you specify via command-line arguments. 

Key features:
- **Flexible model search**: Specify any model names via `-m/--model` flags (can be repeated)
- **Smart pattern matching**: Automatically handles variations in model name formatting (spaces, dashes, dots)
- **Dual loading strategies**: Uses fast static requests by default, automatically falls back to dynamic browser-based loading (Playwright) when needed
- **Anti-bot protection detection**: Recognizes when sites are blocking automated access and reports it clearly
- **State persistence**: Maintains history between runs to detect changes
- **Incremental scanning**: Only rescans for the models you specify, preserving previous results for other models

The script maintains state between runs, so it can detect and report changes:
- New leaderboard URLs added to your bookmarks
- Removed leaderboard URLs  
- Models that newly appear on existing leaderboards
- Models that disappear from leaderboards

### Why this is useful

AI leaderboards are constantly evolving as new models are released and benchmarked. Manually checking dozens of leaderboard sites for new model releases is time-consuming and error-prone. This tool automates that process by:

1. **Staying current**: Automatically detects when anticipated models finally appear on benchmarks
2. **Comprehensive coverage**: Monitors multiple leaderboards simultaneously from your browser bookmarks
3. **Change detection**: Only alerts you to actual changes, reducing noise
4. **Historical tracking**: Maintains a record of what was found when, useful for tracking model rollouts
5. **Robust scraping**: Handles both static and dynamic content, with fallback strategies for difficult sites

### Usage

1. Create a browser bookmarks folder called "Leaderboards" containing URLs of AI leaderboards you want to monitor
2. Export your bookmarks to an HTML file
3. Run with the models you want to search for:

```bash
# Search for Claude 4 models
python check.py bookmarks.html -m "Claude 4 Sonnet" -m "Claude 4 Opus"

# Search for GPT models  
python check.py bookmarks.html -m "GPT-5" -m "GPT-4.5"

# Force dynamic loading for all sites (slower but more thorough)
python check.py bookmarks.html -m "Claude 4 Sonnet" --dynamic
```

### Command-line options

- `bookmarks_file`: Path to exported HTML bookmarks file (required)
- `-m, --model`: Model name to search for (required, can be repeated multiple times)
- `--dynamic`: Force use of dynamic loading (Playwright) for all URLs instead of trying static requests first

### How it works

1. **Pattern building**: Model names are converted to flexible regex patterns that handle common formatting variations
2. **URL extraction**: Parses your bookmarks HTML to find all URLs in the "Leaderboards" folder
3. **Smart scraping**: 
   - First tries fast static HTTP requests
   - Falls back to browser-based dynamic loading if static fails or finds nothing
   - Detects and reports anti-bot protection
4. **State management**: Merges new results with previous findings, only updating the models you're currently scanning
5. **Change reporting**: Shows what's new, removed, or changed since the last run

The script will show current findings and highlight any changes since the last run. State is automatically saved to `leaderboard_state.json`.

### Configuration

Model patterns can be modified in the `model_patterns` dictionary to search for different models or adjust the regex patterns used for detection.
