# constants.py

# Keys for commit analysis
import os
from pathlib import Path

KEY_IS_CONVENTIONAL = "is_conventional"
KEY_COMMITS = "commits"
KEY_CUSTOM_TYPES = "custom_types"
KEY_CC_TYPES = "cc_types"
KEY_ANALYSIS_SUMMARY = "analysis_summary"

SAMPLE_SIZE = 385
MIN_CC_PERCENTAGE = 0.6
MIN_CC_COMMITS = 10
CHUNK_SIZE_PERCENT = 0.05
NUM_CHUNKS = int(1 / CHUNK_SIZE_PERCENT)
MIN_COMMITS_AFTER_CP = 50
MIN_CC_RATE = 0.5

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
DATA = ROOT / "data" / "dataset.json"
COMMIT_ANALYSIS_RESULTS = ROOT / "results" / "commit_messages"
RESULTS = ROOT / "results"
ERROR = ROOT / "results" / "error_log.txt"
TEMP = ROOT / "data" / "temp"
PLOTS = ROOT / "results" / "final_plots"
GITHUB_TOKEN = os.getenv('GITHUB_ACCESS_TOKEN')
