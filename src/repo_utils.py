from git import GitCommandError
from pathlib import Path
import json

from constants import *
from enrich_with_metadata import enrich_commits_with_metadata


def load_commit_messages(repo):
    """
    Lädt Commit-Nachrichten und Datumsangaben von einem Git-Repository.
    """
    try:
        default_branch = repo.active_branch.name
    except TypeError:
        default_branch = "HEAD"

    try:
        return [(commit.committed_datetime, commit.message) for commit in repo.iter_commits(rev=default_branch)]
    except GitCommandError as e:
        print(f"Fehler beim Laden der Commits vom Branch '{default_branch}': {e}")
        return []


def save_commits_to_json(commit_messages, repo_name, results_dir):
    """
    Speichert die Commit-Nachrichten als JSON-Datei und fügt eine Zusammenfassung hinzu.

    Args:
        commit_messages (list): Liste von Tupeln mit (committed_datetime, message).
        repo_name (str): Name des Repositories.
        results_dir (str): Verzeichnis, in dem die Ergebnisse gespeichert werden sollen.

    Returns:
        Path: Pfad zur gespeicherten JSON-Datei.
    """

    file_path_json = Path(results_dir) / f"{repo_name}_commit_messages.json"

    json_serializable_commits = [
        {'committed_datetime': c[0].isoformat(), 'message': c[1]} for c in commit_messages
    ]

    enriched_commits, summary = enrich_commits_with_metadata(json_serializable_commits)

    # Erstelle die gesamte JSON-Datenstruktur
    json_data = {
        KEY_COMMITS: enriched_commits,
        KEY_CUSTOM_TYPES: list(summary[CUSTOM_TYPE_DISTRIBUTION_KEY].keys()),
        KEY_CC_TYPES: list(summary[CC_TYPE_DISTRIBUTION_KEY].keys()),
        KEY_ANALYSIS_SUMMARY: summary
    }

    with open(file_path_json, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    return file_path_json
