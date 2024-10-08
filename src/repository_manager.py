# repository_manager.py

import os
import shutil
import stat
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

def handle_remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clone_repository(repo):
    """
    Klont ein Repository oder lädt es, wenn es bereits vorhanden ist.
    """
    repo_name = repo["name"]
    repo_url = repo["clone_url"]
    repo_language = f"Sprache-{repo['language']}" if repo[
        "language"] else "Sprache_Unknown"  # Fallback, falls Sprache nicht angegeben ist

    # Erstelle den sprachspezifischen Unterordner
    language_dir = Path(TEMP) / repo_language
    language_dir.mkdir(parents=True, exist_ok=True)

    # Definiere die endgültigen und temporären Verzeichnisse
    repo_dir = language_dir / repo_name
    repo_dir_temp = language_dir / f"{repo_name}_temp"

    if repo_dir.exists():
        print(f"Repository {repo_name} bereits vorhanden.")
        try:
            repo = Repo(repo_dir)
            # Optional: Repository aktualisieren
            # repo.remotes.origin.pull()
            return repo
        except GitCommandError as e:
            print(f"Fehler beim Laden des Repositories {repo_name}: {e}")
            return None
    else:
        # Wenn das temporäre Verzeichnis existiert, wurde ein vorheriger Klonvorgang unterbrochen
        if repo_dir_temp.exists():
            print(f"Incomplete repository gefunden. Lösche temporäres Verzeichnis {repo_dir_temp}")
            shutil.rmtree(repo_dir_temp, onerror=handle_remove_readonly)

        print(f"Cloning {repo_name} von {repo_url} in {language_dir}")
        try:
            Repo.clone_from(repo_url, repo_dir_temp, progress=CloneProgress())
            # Benenne das temporäre Verzeichnis in das endgültige Verzeichnis um
            os.rename(repo_dir_temp, repo_dir)
            return Repo(repo_dir)
        except GitCommandError as e:
            # Fange Git-Fehler ab, wie z.B. deaktivierte Repositories oder Fehler beim Klonen
            print(f"Fehler beim Klonen des Repositories {repo_name}: {e}")
            if "Repository not found" in str(e) or "Repository disabled" in str(e):
                print(f"Das Repository {repo_name} ist entweder deaktiviert oder nicht mehr verfügbar.")
            else:
                print(f"Ein allgemeiner Git-Fehler ist aufgetreten: {e}")
            return None


def delete_temp():
    """
    Löscht das TEMP-Verzeichnis.
    """
    try:
        shutil.rmtree(TEMP_DIR)
    except OSError as e:
        print(f"Fehler beim Löschen von {TEMP_DIR}: {e}")
