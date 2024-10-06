from pathlib import Path
from load_dataset import load_dataset
from process_utils import process_repo
from visualization_utils import plot_cc_adoption_dates

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
RESULTS = ROOT / "results" / "commit_messages"
YAML = ROOT / "data" / "test.yaml"


if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    repos = load_dataset(YAML)

    for repo_data in repos:
        process_repo(repo_data, RESULTS)

    plot_cc_adoption_dates(RESULTS)
