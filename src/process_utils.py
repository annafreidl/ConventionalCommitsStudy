import json
from pathlib import Path

from is_using_cc import search_for_cc_indications

"""
Logik zum Verarbeiten der Repositories,
inklusive dem Klonen, dem Laden von Commits und der Visualisierung.
"""
from git import GitCommandError

from analysis import find_80_percent_conventional_date, calculate_monthly_conventional_commits
from clone_repos import clone_repo
from enrich_with_metadata import enrich_commits_with_metadata
from repo_utils import load_commit_messages, save_commits_to_json
from visualization_utils import visualize_repo_commits, visualize_monthly_conventional_commits


def process_repo(repo_data, results_dir):
    """
    Verarbeitet ein Repository, klont es, lädt die Commits, reichert sie an, speichert sie als JSON
    und erstellt Visualisierungen.
    """
    cloned_repo = clone_repo(repo_data)

    if cloned_repo is None:
        print(f"Überspringe Repository {repo_data['name']} aufgrund eines Klonfehlers.")
        return

    result_path = Path(results_dir)/f"{repo_data['name']}_commit_messages.json"

    if not result_path.exists():
        try:
            # Lade die Commits mit der aktualisierten Funktion
            commit_messages = load_commit_messages(cloned_repo)

            # Reiche die Commits direkt an
            enriched_commits, summary = enrich_commits_with_metadata(commit_messages)
        except (AttributeError, GitCommandError) as e:
            print(f"Fehler beim Laden der Commit-Nachrichten für {repo_data['name']}: {e}")
            return

        repo_name = repo_data["name"].replace("/", "_")

        # Speichern der angereicherten Commits als JSON
        file_path_json = save_commits_to_json(enriched_commits, summary, repo_name, results_dir)

    # Weitere Verarbeitung oder Visualisierung hier
        monthly_cc_type_percentage, monthly_custom_type_percentage = calculate_monthly_conventional_commits(enriched_commits)
        #visualize_monthly_conventional_commits(monthly_cc_type_percentage, monthly_custom_type_percentage)

        # Visualisierung
        # visualize_repo_commits(file_path_json, summary, repo_name)

    # Öffne und lade die JSON-Datei
    with open(result_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Navigiere zum 'analysis_summary'
    analysis_summary = data.get("analysis_summary", {})

    # Hole den Wert von 'cc_adoption_date'
    cc_adoption_date = analysis_summary.get("cc_adoption_date", None)

    if cc_adoption_date is not None:
        print(f"\n CC-Einführungsdatum: {cc_adoption_date}\n")

    else: print(f"Commits für {repo_data['name']} bereits vorhanden.")

    using_cc = search_for_cc_indications(cloned_repo)
    print(f"Repository verwendet Conventional Commits: {using_cc}")
