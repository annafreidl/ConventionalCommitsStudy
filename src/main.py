from pathlib import Path
from load_dataset import load_dataset
from process_utils import process_repo
from visualization_utils import plot_cc_adoption_dates

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
RESULTS = ROOT / "results" / "commit_messages"
YAML = ROOT / "data" / "dataset.yaml"


if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    repos = load_dataset(YAML)

    # organize_existing_repos(repos)

    i = 0

    for repo_data in repos:
        i += 1
        process_repo(repo_data, RESULTS)
        print(f"Processed {i} repos")

    plot_cc_adoption_dates(RESULTS)
