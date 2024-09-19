from git import GitCommandError
from pathlib import Path
import json
from constants import *
from enrich_with_metadata import enrich_commits_with_metadata
import datetime


def load_commit_messages(repo):
    """
    Lädt Commit-Daten aus einem Git-Repository, einschließlich Datum, Nachricht, Autor, Einfügungen und Löschungen.
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
        i = 0
        while i < len(lines):
            line = lines[i]
            if ';' in line:
                parts = line.split(';')
                if len(parts) >= 4:
                    commit_hash = parts[0]
                    timestamp = int(parts[1])
                    committed_datetime = datetime.datetime.utcfromtimestamp(timestamp).isoformat()
                    author = parts[2]
                    message = parts[3]
                    i += 1
                    insertions = 0
                    deletions = 0
                    while i < len(lines) and lines[i].strip() == '':
                        i += 1
                    if i < len(lines) and ('file changed' in lines[i] or 'files changed' in lines[i]):
                        stat_line = lines[i].strip()
                        if 'insertion' in stat_line:
                            insertions = int(stat_line.split('insertion')[0].split(',')[-1].strip())
                        if 'deletion' in stat_line:
                            deletions = int(stat_line.split('deletion')[0].split(',')[-1].strip())
                        i += 1
                    commit_data = {
                        'committed_datetime': committed_datetime,
                        'message': message.strip(),
                        'author': author.strip(),
                        'insertions': insertions,
                        'deletions': deletions
                    }
                    commits.append(commit_data)
                else:
                    i += 1
            else:
                i += 1

        return commits
    except GitCommandError as e:
        print(f"Fehler beim Laden der Commits: {e}")
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

    enriched_commits, summary = enrich_commits_with_metadata(commit_messages)

    # Erstelle die gesamte JSON-Datenstruktur
    json_data = {
        KEY_COMMITS: enriched_commits,
        KEY_CUSTOM_TYPES: list(summary[CUSTOM_TYPE_DISTRIBUTION_KEY].keys()),
        KEY_CC_TYPES: list(summary[CC_TYPE_DISTRIBUTION_KEY].keys()),
        KEY_ANALYSIS_SUMMARY: summary
    }

    with open(file_path_json, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
        f.flush()  # Leert den Puffer
    return file_path_json
