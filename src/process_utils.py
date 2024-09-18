"""
Logik zum Verarbeiten der Repositories,
inklusive dem Klonen, dem Laden von Commits und der Visualisierung.
"""
from git import GitCommandError

from clone_repos import clone_repo
from repo_utils import load_commit_messages, save_commits_to_json


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
    except (AttributeError, GitCommandError) as e:
        print(f"Fehler beim Laden der Commit-Nachrichten für {repo_data['name']}: {e}")
        return

    repo_name = repo_data["name"].replace("/", "_")

    # Speichern der Commits mit Metadaten als JSON
    file_path_json = save_commits_to_json(commit_messages, repo_name, results_dir)

    # Visualisierung
    # visualize_repo_commits(file_path_json, repo_name)
