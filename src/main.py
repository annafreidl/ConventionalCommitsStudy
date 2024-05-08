from pathlib import Path

from load_dataset import load_dataset
from clone_repos import clone_repo
from commit_diffs import load_diffs

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
RESULTS = f"{ROOT}/results"
YAML = f"{ROOT}/data/sample.yaml"

if __name__ == "__main__":
    Path(RESULTS).mkdir(exist_ok=True)
    repos = load_dataset(YAML)

    repo_stats = []
    for repo in repos:
        cloned_repo = clone_repo(repo)
        diffs = load_diffs(cloned_repo, length=None)
        # TODO
