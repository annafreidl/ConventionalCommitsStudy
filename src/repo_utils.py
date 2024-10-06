from pathlib import Path
import json
from constants import *
from enrich_with_metadata import enrich_commits_with_metadata
from git import GitCommandError
import datetime

def load_commit_messages(repo):
    """
    Lädt Commit-Daten aus einem Git-Repository, einschließlich Datum, Nachricht, Autor, Einfügungen und Löschungen.
    Verwendet 'git log --numstat', um die Daten effizient zu laden.
    """
    commits = []
    try:
        default_branch = repo.active_branch.name
    except (TypeError, AttributeError):
        default_branch = "HEAD"

    try:
        git_log_output = repo.git.log(
            default_branch,
            pretty="%H;%ct;%cn;%s",
            shortstat=True
        )

        lines = git_log_output.split('\n')
        current_commit = None
        for line in lines:
            if ';' in line:
                # Start eines neuen Commits
                parts = line.strip().split(';')
                if len(parts) >= 4:
                    commit_hash = parts[0]
                    timestamp = int(parts[1])
                    committed_datetime = datetime.datetime.utcfromtimestamp(timestamp).isoformat()
                    author = parts[2]
                    message = parts[3]
                    current_commit = {
                        'committed_datetime': committed_datetime,
                        'message': message.strip(),
                        'author': author.strip(),
                        'insertions': 0,
                        'deletions': 0
                    }
                    commits.append(current_commit)
            elif line.strip() and current_commit:
                # Verarbeitung der numstat-Zeilen
                parts = line.strip().split('\t')
                if len(parts) == 3:
                    insertions_str, deletions_str, filename = parts
                    insertions = int(insertions_str) if insertions_str.isdigit() else 0
                    deletions = int(deletions_str) if deletions_str.isdigit() else 0
                    current_commit['insertions'] += insertions
                    current_commit['deletions'] += deletions
        return commits
    except GitCommandError as e:
        print(f"Fehler beim Laden der Commits: {e}")
        return []



def save_commits_to_json(enriched_commits, summary, repo_name, results_dir):
    """
    Speichert die angereicherten Commits und die Zusammenfassung als JSON-Datei.

    Args:
        enriched_commits (list): Liste der angereicherten Commits.
        summary (dict): Zusammenfassung der Analyse.
        repo_name (str): Name des Repositories.
        results_dir (str): Verzeichnis, in dem die Ergebnisse gespeichert werden sollen.

    Returns:
        Path: Pfad zur gespeicherten JSON-Datei.
    """

    file_path_json = Path(results_dir) / f"{repo_name}_commit_messages.json"

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

