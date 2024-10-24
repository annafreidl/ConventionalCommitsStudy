import json

from constants import ROOT
from repository_manager import clone_repository, delete_temp
from commit_loader import load_commits
from data_enricher import enrich_commits, should_analyze_cc_adoption
from data_saver import save_to_json, load_from_json
from analyzer import classify_repository, check_homepage_for_cc
from analyzer import search_for_cc_indications
from testing import analyse_commit_chunks, binary_segmentation_date_analysis
from pathlib import Path
from typing import Dict, Any, Optional
import logging


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


def process_repository(repo_data: Dict[str, Any], results_dir: Path) -> None:
    """
    Verarbeitet ein Repository, indem es Daten lädt, analysiert und klassifiziert.

    Schritte:
    1. Extrahiert Metadaten aus repo_data.
    2. Klont oder lädt das Repository.
    3. Lädt oder erstellt die Commit-Daten.
    4. Analysiert die Commits auf die Einführung von Conventional Commits.
    5. Sucht nach Hinweisen auf die Verwendung von Conventional Commits.
    6. Klassifiziert das Repository basierend auf der Analyse.
    7. Zeichnet die Klassifikation auf.

    Args:
        repo_data (Dict[str, Any]): Die Metadaten des Repositories.
        results_dir (Path): Das Verzeichnis, in dem Ergebnisse gespeichert werden.
    """
    repo_name = repo_data.get("name", "Unknown").replace("/", "_")
    language = repo_data.get("language", "Unknown")
    size = repo_data.get("size", 0)
    repo_id = repo_data.get("id", 0)
    owner = repo_data.get("owner", {})
    pushed_at = repo_data.get("pushed_at", "")
    created_at = repo_data.get("created_at", "")
    updated_at = repo_data.get("updated_at", "")
    forks_count = repo_data.get("forks_count", 0)
    homepage = repo_data.get("homepage")

    json_file_path = results_dir / f"{repo_name}_commit_messages.json"

    logging.info(f"Verarbeite Repository {repo_name}...")

    # Versuche, das Repository zu laden oder zu klonen
    repo = clone_repository(repo_data)
    if repo is None:
        logging.warning(f"Konnte Repository {repo_name} nicht klonen oder laden.")
        return

    # Lade oder erstelle die Commit-Daten
    if json_file_path.exists():
        logging.info(f"JSON-Datei für {repo_name} bereits vorhanden.")
        data = load_from_json(json_file_path)
    else:
        logging.info(f"Lade und analysiere Commits für {repo_name}...")
        commits = load_commits(repo)
        enriched_commits, summary = enrich_commits(commits)
        # Ergänze die Zusammenfassung mit zusätzlichen Metadaten
        summary.update({
            "language": language,
            "size": size,
            "id": repo_id,
            "owner": owner,
            "pushed_at": pushed_at,
            "created_at": created_at,
            "updated_at": updated_at,
            "forks_count": forks_count,
        })
        save_to_json(enriched_commits, summary, repo_name, results_dir)
        data = {"commits": enriched_commits, "analysis_summary": summary}

    analysis_summary = data.get("analysis_summary", {})
    cc_adoption_date = analysis_summary.get("cc_adoption_date")

    if cc_adoption_date:
        logging.info(f"CC-Einführungsdatum für {repo_name}: {cc_adoption_date}")
    else:
        logging.info(f"Keine CC-Einführung in {repo_name} festgestellt.")

    # Suche nach Hinweisen auf die Verwendung von Conventional Commits
    using_cc = search_for_cc_indications(repo)

    if homepage:
        logging.info(f"Überprüfe Homepage {homepage} für {repo_name} auf Hinweise zu CC.")
        homepage_uses_cc = check_homepage_for_cc(homepage)
        using_cc = using_cc or homepage_uses_cc
    else:
        logging.info(f"Keine Homepage angegeben für {repo_name}. Überspringe die Homepage-Prüfung.")

    if using_cc:
        logging.info(f"Repository {repo_name} erwähnt die Verwendung von Conventional Commits.")

    # Klassifiziere das Repository basierend auf der Analyse
    classification = classify_repository(analysis_summary, using_cc)
    logging.info(f"Das Repository {repo_name} wird klassifiziert als: {classification}")

    # Klassifikation aufzeichnen
    record_classification(repo_name, language, classification)
