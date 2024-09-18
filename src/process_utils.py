"""
Logik zum Verarbeiten der Repositories,
inklusive dem Klonen, dem Laden von Commits und der Visualisierung.
"""

from clone_repos import clone_repo
from json_utils import load_json
from repo_utils import load_commit_messages, save_commits_to_json
from visualization_utils import visualize_repo_commits


def process_repo(repo_data, results_dir):
    """
    Verarbeitet ein Repository, klont es, lädt die Commits, speichert sie als JSON
    und erstellt Visualisierungen.
    """
    cloned_repo = clone_repo(repo_data)

    if cloned_repo is None:
        print(f"Überspringe Repository {repo_data['name']} aufgrund eines Klonfehlers.")
        return

    try:
        commit_messages = load_commit_messages(cloned_repo)
    except AttributeError as e:
        print(f"Fehler beim Laden der Commit-Nachrichten für {repo_data['name']}: {e}")
        return

    repo_name = repo_data["name"].replace("/", "_")

    # Speichern der Commits mit Metadaten als JSON
    file_path_json = save_commits_to_json(commit_messages, repo_name, results_dir)

    # JSON-Daten laden und visualisieren
    commits_from_json = load_json(file_path_json)
    # if commits_from_json:
    #      visualize_repo_commits(commits_from_json, repo_name)
