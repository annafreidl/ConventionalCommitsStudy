# data_saver.py
import json
import os
from pathlib import Path

from constants import DATA


def load_dataset():
    """Load the main dataset JSON file containing repository metadata."""
    with open(DATA, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_to_json(enriched_commits, summary, file_path):
    """
    Speichert die angereicherten Commits und die Zusammenfassung als JSON.

    Args:
        enriched_commits (list): Liste der angereicherten Commits.
        summary (dict): Zusammenfassung der Analyse.
        repo_name (str): Name des Repositories.
        results_dir (str): Verzeichnis für die Ergebnisse.

    Returns:
        :param summary:
        :param enriched_commits:
        :param file_path:
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
