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

    # Bestimme den Namen der JSON-Datei basierend auf dem Repository-Namen
    repo_name = repo_data["name"].replace("/", "_")
    result_path = Path(results_dir) / f"{repo_name}_commit_messages.json"

    if not result_path.exists():
        try:
            # Lade die Commits mit der aktualisierten Funktion
            commit_messages = load_commit_messages(cloned_repo)

            # Reiche die Commits direkt an
            enriched_commits, summary = enrich_commits_with_metadata(commit_messages)

            # Speichern der angereicherten Commits als JSON
            save_commits_to_json(enriched_commits, summary, repo_name, results_dir)
        except (AttributeError, GitCommandError) as e:
            print(f"Fehler beim Laden der Commit-Nachrichten für {repo_data['name']}: {e}")
            return
    else:
        print(f"Commits für {repo_data['name']} bereits vorhanden.")

    # Öffne und lade die JSON-Datei
    try:
        with open(result_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except Exception as e:
        print(f"Fehler beim Laden der JSON-Datei {result_path}: {e}")
        return

    # Navigiere zum 'analysis_summary'
    analysis_summary = data.get("analysis_summary", {})

    # Hole den Wert von 'cc_adoption_date'
    cc_adoption_date = analysis_summary.get("cc_adoption_date", None)

    if cc_adoption_date is not None:
        print(f"\nCC-Einführungsdatum: {cc_adoption_date}\n")
    else:
        print(f"Keine CC-Einführung in {repo_data['name']} festgestellt.")

    # Überprüfe, ob das Repository Conventional Commits verwendet
    using_cc = search_for_cc_indications(cloned_repo)
    print(f"Repository verwendet Conventional Commits: {using_cc}")

    # Klassifiziere das Repository
    classification = classify_repository(analysis_summary, using_cc)
    print(f"Das Repository {repo_data['name']} wird klassifiziert als: {classification}")

    # Hier kannst du die Klassifikation speichern oder weitere Aktionen durchführen


def classify_repository(analysis_summary, using_cc):
    total_commits = analysis_summary.get("total_commits", 0)
    adoption_date_exists = False
    if (analysis_summary.get("cc_adoption_date", 0)) is not None:
        adoption_date_exists = True

    if not using_cc and not adoption_date_exists:
        return "nicht conventional"
    elif not using_cc and adoption_date_exists:
        return "nutzen CC, aber nicht als Vorgabe erkennbar"
    elif using_cc and adoption_date_exists:
        return "nutzen CC und als Vorgabe erkennbar"
    elif using_cc and not adoption_date_exists:
        return "Vorgabe/Erwähnung von CC, aber wird nicht genutzt"
    else:
        return "nicht eindeutig klassifizierbar"
