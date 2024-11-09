# constants.py
import os
from pathlib import Path

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
