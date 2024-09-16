import os
import shutil
from pathlib import Path
from git import Repo, GitCommandError
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
        try:
            return Repo.clone_from(repo_url, repo_dir, progress=CloneProgress())
        except GitCommandError as e:
            # Fange Git-Fehler ab, wie z.B. deaktivierte Repositories oder Fehler beim Klonen
            print(f"Fehler beim Klonen des Repositories {repo_name}: {e}")
            if "Repository not found" in str(e) or "Repository disabled" in str(e):
                print(f"Das Repository {repo_name} ist entweder deaktiviert oder nicht mehr verfügbar.")
            else:
                print(f"Ein allgemeiner Git-Fehler ist aufgetreten: {e}")
            return None
    else:
        print(f"Repository {repo_name} already exists")
        return Repo(repo_dir)


def delete_temp():
    try:
        shutil.rmtree(TEMP)
    except OSError as e:
        print(f"{e.filename}: {e.strerror}")
