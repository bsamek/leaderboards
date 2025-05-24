# Tools for LLM leaderboards

## check.py

A monitoring tool that tracks when new AI models appear on leaderboard websites.

### What it does

`check.py` scans a collection of AI leaderboard URLs (stored in your browser bookmarks) and searches for mentions of specific AI models. It currently looks for:

- Claude 4 Sonnet
- Claude 4 Opus

The script maintains state between runs, so it can detect and report changes:
- New leaderboard URLs added to your bookmarks
- Removed leaderboard URLs
- Models that newly appear on existing leaderboards
- Models that disappear from leaderboards

### Why this is useful

AI leaderboards are constantly evolving as new models are released and benchmarked. Manually checking dozens of leaderboard sites for new model releases is time-consuming and error-prone. This tool automates that process by:

1. **Staying current**: Automatically detects when anticipated models (like Claude 4) finally appear on benchmarks
2. **Comprehensive coverage**: Monitors multiple leaderboards simultaneously from your browser bookmarks
3. **Change detection**: Only alerts you to actual changes, reducing noise
4. **Historical tracking**: Maintains a record of what was found when, useful for tracking model rollouts

### Usage

1. Create a browser bookmarks folder called "Leaderboards" containing URLs of AI leaderboards you want to monitor
2. Export your bookmarks to an HTML file
3. Run: `python check.py path/to/bookmarks.html`

The script will show current findings and highlight any changes since the last run. State is automatically saved to `leaderboard_state.json`.

### Configuration

Model patterns can be modified in the `model_patterns` dictionary to search for different models or adjust the regex patterns used for detection.
