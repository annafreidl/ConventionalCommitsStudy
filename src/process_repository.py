import json

from constants import ROOT
from repository_manager import clone_repository, delete_temp
from commit_loader import load_commits
from data_enricher import enrich_commits, should_analyze_cc_adoption
from data_saver import save_to_json, load_from_json
from analyzer import classify_repository
from analyzer import search_for_cc_indications
from testing import analyse_commit_chunks, binary_segmentation_date_analysis


def record_classification(repo_name, language, classification):
    """
    Zeichnet die Klassifikation eines Repositories nach Sprache auf.

    Args:
        repo_name (str): Der Name des Repositories.
        language (str): Die Programmiersprache des Repositories.
        classification (str): Die Klassifikationskategorie.
    """
    classification_file = ROOT / "results" / "repository_classifications.json"
    if classification_file.exists():
        with open(classification_file, 'r', encoding='utf-8') as f:
            classifications = json.load(f)
    else:
        classifications = {}

    # Wenn die Sprache noch nicht vorhanden ist, initialisiere sie
    if language not in classifications:
        classifications[language] = {}

    # Weise die Klassifikation dem Repository zu
    classifications[language][repo_name] = classification

    with open(classification_file, 'w', encoding='utf-8') as f:
        json.dump(classifications, f, indent=2)


def process_repository(repo_data, RESULTS_DIR):
    repo_name = repo_data["name"].replace("/", "_")
    language = repo_data.get('language', 'Unknown')
    json_file_path = RESULTS_DIR / f"{repo_name}_commit_messages.json"

    # Versuche, das Repository zu laden oder zu klonen
    repo = clone_repository(repo_data)
    if repo is None:
        return

    if json_file_path.exists():
        print(f"JSON-Datei für {repo_name} bereits vorhanden.")
        data = load_from_json(json_file_path)
        summary = data.get("analysis_summary", {})
    else:
        # Lade die Commits und reiche sie an
        commits = load_commits(repo)
        enriched_commits, summary = enrich_commits(commits)
        save_to_json(enriched_commits, summary, repo_name, RESULTS_DIR)
        data = {"commits": enriched_commits, "analysis_summary": summary}

    if should_analyze_cc_adoption(summary):
        print(f"Analysiere nach CC-Einführungsdatum für {repo_name}")
        binary_segmentation_date_analysis(data)

    analysis_summary = data.get("analysis_summary", {})
    cc_adoption_date = analysis_summary.get("cc_adoption_date")
    if cc_adoption_date:
        print(f"CC-Einführungsdatum für {repo_name}: {cc_adoption_date}")

    else:
        print(f"Keine CC-Einführung in {repo_name} festgestellt.")

    using_cc = search_for_cc_indications(repo)
    print(f"Repository {repo_name} verwendet Conventional Commits: {using_cc}")

    classification = classify_repository(analysis_summary, using_cc)
    print(f"Das Repository {repo_name} wird klassifiziert als: {classification}")

    # Klassifikation aufzeichnen
    record_classification(repo_name, language, classification)
