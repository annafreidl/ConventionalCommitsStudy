# data_saver.py
import json
import logging
import os

import yaml
from pathlib import Path

from constants import DATA


def save_to_json(enriched_commits, summary, file_path):
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
    json_data = {
        "commits": enriched_commits,
        "custom_types": list(summary['custom_type_distribution'].keys()),
        "cc_types": list(summary['cc_type_distribution'].keys()),
        "analysis_summary": summary
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    return file_path

def load_repository_data(json_file_path):
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    return data

def load_all_repositories_data(json_directory_path):
    repository_data_list = []
    for filename in os.listdir(json_directory_path):
        if filename.endswith('.json'):
            json_file_path = os.path.join(json_directory_path, filename)
            repo_data = load_repository_data(json_file_path)
            repository_data_list.append(repo_data)
    return repository_data_list

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


def load_analysis_summaries(results_dir):
    summaries = []
    for filename in os.listdir(results_dir):
        filepath = os.path.join(results_dir, filename)
        with open(filepath, 'r') as f:
            # logging.info(f"Loading summary from {filepath}")
            data = json.load(f)
            repo_name = filename.replace('_commit_messages.json', '')
            summary = data.get('analysis_summary', {})
            summary['repo_name'] = repo_name
            summaries.append(summary)
    return summaries
