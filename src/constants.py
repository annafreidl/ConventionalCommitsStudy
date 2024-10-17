# constants.py

# Keys for commit analysis
from pathlib import Path

KEY_IS_CONVENTIONAL = "is_conventional"
KEY_COMMITS = "commits"
KEY_CUSTOM_TYPES = "custom_types"
KEY_CC_TYPES = "cc_types"
KEY_ANALYSIS_SUMMARY = "analysis_summary"

# Keys for analysis summary
TOTAL_COMMITS_KEY = 'total_commits'
CONVENTIONAL_COMMITS_KEY = 'conventional_commits'
UNCONVENTIONAL_COMMITS_KEY = 'unconventional_commits'
CUSTOM_TYPE_DISTRIBUTION_KEY = 'custom_type_distribution'
CC_TYPE_DISTRIBUTION_KEY = 'cc_type_distribution'

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
RESULTS = ROOT / "results" / "commit_messages"
YAML = ROOT / "data" / "dataset.yaml"

SAMPLE_SIZE = 385
MIN_CC_PERCENTAGE = 0.6
MIN_CC_COMMITS = 10
CHUNK_SIZE_PERCENT = 0.05
NUM_CHUNKS = int(1 / CHUNK_SIZE_PERCENT)
MIN_COMMITS_AFTER_CP = 50
MIN_CC_RATE = 0.5
