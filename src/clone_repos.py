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


def clone_repo(repo):
    """
    Klont ein Git-Repository in einen sprachspezifischen Ordner innerhalb von TEMP.

    Args:
        repo (dict): Ein Dictionary mit Informationen zum Repository, einschließlich 'name', 'clone_url' und 'language'.

    Returns:
        Repo oder None: Das geklonte Repository-Objekt oder None bei Fehlern.
    """
    repo_name = repo["name"]
    repo_url = repo["clone_url"]
    repo_language = f"Sprache-{repo['language']}" if repo["language"] else "Sprache_Unknown"  # Fallback, falls Sprache nicht angegeben ist

    # Erstelle den sprachspezifischen Unterordner
    language_dir = Path(TEMP) / repo_language
    language_dir.mkdir(parents=True, exist_ok=True)

    # Definiere die endgültigen und temporären Verzeichnisse
    repo_dir = language_dir / repo_name
    repo_dir_temp = language_dir / f"{repo_name}_temp"

    if repo_dir.exists():
        print(f"Repository {repo_name} bereits vorhanden in {repo_language}")
        try:
            return Repo(repo_dir)
        except GitCommandError as e:
            print(f"Fehler beim Zugriff auf das Repository {repo_name}: {e}")
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
    try:
        shutil.rmtree(TEMP)
    except OSError as e:
        print(f"{e.filename}: {e.strerror}")

def organize_existing_repos(repos):
    """
    Überprüft vorhandene Repositories im TEMP-Ordner und verschiebt sie in die entsprechenden Sprachordner.

    Args:
        repos (list): Eine Liste von Dictionaries mit Repository-Informationen, einschließlich 'name' und 'language'.
    """
    for repo in repos:
        repo_name = repo["name"]
        repo_language = f"Sprache-{repo['language']}" if repo["language"] else "Sprache Unknown"
        current_repo_dir = Path(TEMP) / repo_name

        if current_repo_dir.exists() and current_repo_dir.is_dir():
            target_language_dir = Path(TEMP) / repo_language
            target_repo_dir = target_language_dir / repo_name

            # Überprüfe, ob das Repository bereits im richtigen Ordner ist
            if not target_repo_dir.exists():
                # Erstelle den Sprachordner, falls nicht vorhanden
                target_language_dir.mkdir(parents=True, exist_ok=True)

                print(f"Verschiebe {repo_name} von {current_repo_dir} nach {target_repo_dir}")
                try:
                    shutil.move(str(current_repo_dir), str(target_repo_dir))
                    print(f"{repo_name} erfolgreich verschoben.")
                except Exception as e:
                    print(f"Fehler beim Verschieben von {repo_name}: {e}")

