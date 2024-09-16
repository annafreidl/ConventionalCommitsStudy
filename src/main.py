from pathlib import Path
from load_dataset import load_dataset
from process_utils import process_repo

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
RESULTS = ROOT / "results" / "commit_messages"
YAML = ROOT / "data" / "dataset.yaml"


if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    repos = load_dataset(YAML)

    for repo_data in repos:
        process_repo(repo_data, RESULTS)
