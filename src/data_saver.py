# data_saver.py

import json
import yaml
from pathlib import Path


def save_to_json(enriched_commits, summary, repo_name, results_dir):
    """
    Speichert die angereicherten Commits und die Zusammenfassung als JSON.

    Args:
        enriched_commits (list): Liste der angereicherten Commits.
        summary (dict): Zusammenfassung der Analyse.
        repo_name (str): Name des Repositories.
        results_dir (str): Verzeichnis für die Ergebnisse.

    Returns:
        Path: Pfad zur gespeicherten JSON-Datei.
    """
    file_path = Path(results_dir) / f"{repo_name}_commit_messages.json"
    json_data = {
        "commits": enriched_commits,
        "custom_types": list(summary['custom_type_distribution'].keys()),
        "cc_types": list(summary['cc_type_distribution'].keys()),
        "analysis_summary": summary
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    return file_path


def load_from_json(file_path):
    """
    Lädt Daten aus einer JSON-Datei.

    Args:
        file_path (Path): Pfad zur JSON-Datei.

    Returns:
        dict: Geladene Daten.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


def load_dataset(yaml_path):
    json_path = Path(yaml_path).with_suffix('.json')

    if not json_path.exists():

        with open(yaml_path, "r", encoding='utf-8') as file:
            data = yaml.safe_load(file)

        extracted_data = [
            {"name": d["name"], "clone_url": d["clone_url"], "language": d["language"]}
            for d in data if "name" in d and "clone_url" in d and "language" in d
        ]

        with open(json_path, "w", encoding='utf-8') as file:
            json.dump(extracted_data, file, indent=4)

        print("Loaded dataset from YAML file")
    else:
        with open(json_path, "r") as file:
            extracted_data = json.load(file)

    return extracted_data


def load_classifications(classification_file):
    """
    Lädt die Repository-Klassifikationen nach Sprache.

    Args:
        classification_file (Path): Pfad zur JSON-Datei mit den Klassifikationen.

    Returns:
        dict: Dictionary mit Sprache als Schlüssel und Repository-Klassifikationen als Wert.
    """
    with open(classification_file, 'r', encoding='utf-8') as f:
        classifications = json.load(f)
    return classifications

