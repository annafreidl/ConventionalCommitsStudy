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
            repo_instance = Repo(repo_dir)
            # Optional: Repository aktualisieren
            # repo.remotes.origin.pull()
        except GitCommandError as e:
            print(f"Fehler beim Laden des Repositories {repo_name}: {e}")
            repo_instance = None
    else:
        # Wenn das temporäre Verzeichnis existiert, wurde ein vorheriger Klonvorgang unterbrochen
        if repo_dir_temp.exists():
            print(f"Incomplete repository gefunden. Lösche temporäres Verzeichnis {repo_dir_temp}")
            shutil.rmtree(repo_dir_temp, onerror=handle_remove_readonly)

        print(f"Cloning {repo_name} von {repo_url} in {language_dir}")
        try:
            repo_instance = Repo.clone_from(repo_url, repo_dir_temp, progress=CloneProgress())
            # Benenne das temporäre Verzeichnis in das endgültige Verzeichnis um
            os.rename(repo_dir_temp, repo_dir)
            # Lade das geklonte Repository neu
            repo_instance = Repo(repo_dir)
        except GitCommandError as e:
            # Fange Git-Fehler ab, wie z.B. deaktivierte Repositories oder Fehler beim Klonen
            print(f"Fehler beim Klonen des Repositories {repo_name}: {e}")
            if "Repository not found" in str(e) or "Repository disabled" in str(e):
                print(f"Das Repository {repo_name} ist entweder deaktiviert oder nicht mehr verfügbar.")
            else:
                print(f"Ein allgemeiner Git-Fehler ist aufgetreten: {e}")
            return None

        # Wenn das Repository ein Wiki hat, klone das Wiki-Repository
    if repo.get("has_wiki", False):
        wiki_url = repo_url.replace(".git", ".wiki.git")
        wiki_dir = repo_dir / ".wiki"

        if wiki_dir.exists():
            print(f"Wiki-Repository für {repo_name} bereits vorhanden.")
            # Optional: Wiki aktualisieren
            try:
                wiki_repo = Repo(wiki_dir)
                # wiki_repo.remotes.origin.pull()
            except GitCommandError as e:
                print(f"Fehler beim Laden des Wiki-Repositories für {repo_name}: {e}")
        else:
            print(f"Cloning Wiki for {repo_name} von {wiki_url}")
            try:
                wiki_repo = Repo.clone_from(wiki_url, wiki_dir)
            except GitCommandError as e:
                print(f"Fehler beim Klonen des Wiki-Repositories für {repo_name}: {e}")
                if "Repository not found" in str(e) or "Repository disabled" in str(e):
                    print(f"Das Wiki-Repository für {repo_name} ist entweder deaktiviert oder nicht verfügbar.")
                else:
                    print(f"Ein allgemeiner Git-Fehler ist aufgetreten: {e}")
                # Wir fahren fort, auch wenn das Wiki nicht geklont werden konnte

    return repo_instance


def delete_temp():
    """
    Löscht das TEMP-Verzeichnis.
    """
    try:
        shutil.rmtree(TEMP_DIR)
    except OSError as e:
        print(f"Fehler beim Löschen von {TEMP_DIR}: {e}")
