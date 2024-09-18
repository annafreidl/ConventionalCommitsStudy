from git import GitCommandError
from pathlib import Path
import json
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
    Speichert die Commit-Nachrichten als JSON-Datei.
    """
    file_path_json = Path(results_dir) / f"{repo_name}_commit_messages.json"
    json_serializable_commits = [
        {'committed_datetime': c[0].isoformat(), 'message': c[1]} for c in commit_messages
    ]

    enriched_commits, summary = enrich_commits_with_metadata(json_serializable_commits)

    # Erstelle die gesamte JSON-Datenstruktur
    json_data = {
        "commits": enriched_commits,
        "custom_types": list(summary['custom_type_distribution'].keys()),
        "cc_types": list(summary['cc_type_distribution'].keys()),
        "analysis_summary": summary
    }

    with open(file_path_json, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    return file_path_json
