import os
import shutil
from pathlib import Path
from git import Repo
from git.remote import RemoteProgress
from tqdm import tqdm


FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]
TEMP = f"{ROOT}/data/temp"


class CloneProgress(RemoteProgress):
    def __init__(self):
        super().__init__()
        self.pbar = tqdm()

    def update(self, op_code, cur_count, max_count=None, message=""):
        self.pbar.total = max_count
        self.pbar.n = cur_count
        self.pbar.refresh()


def clone_repo(repo):
    Path(TEMP).mkdir(parents=True, exist_ok=True)

    repo_name = repo["name"]
    repo_url = repo["clone_url"]
    repo_dir = f"{TEMP}/{repo_name}"

    if not os.path.exists(repo_dir):
        print(f"Cloning {repo_name} from {repo_url}")
        return Repo.clone_from(repo_url, repo_dir, progress=CloneProgress())
    else:
        print(f"Repository {repo_name} already exists")
        return Repo(repo_dir)


def delete_temp():
    try:
        shutil.rmtree(TEMP)
    except OSError as e:
        print(f"{e.filename}: {e.strerror}")
