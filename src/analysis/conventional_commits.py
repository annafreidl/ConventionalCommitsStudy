import math
import re
from collections import defaultdict
from datetime import datetime
from conventional_pre_commit.format import is_conventional

# Globale Liste zum Speichern der benutzerdefinierten Typen
from json_utils import load_json

custom_types = []


def is_conventional_commit(commit_message):
    """
    Prüft, ob eine Commit-Nachricht der CC-Convention entspricht.
    """

    # wichtig, dass die Nachricht in Kleinbuchstaben umgewandelt wird,
    # damit alle Typen mit is_conventional gefunden werden
    commit_message = commit_message.lower()

    # Unterscheidung zwischen custom und CC
    if is_conventional(commit_message):
        return True
    else:
        return False


def is_conventional_custom(commit_message):
    """
    Prüft, ob eine Commit-Nachricht der CC-Convention mit custom Typen entspricht.
    """
    pattern = r"^([a-zA-Z]+)(?:\(([\w\-\.\s]+)\))?!?: .+"

    match = re.match(pattern, commit_message.lower())
    if match:
        custom_type = match.group(1)
        custom_types.append(custom_type)  # Füge den Typ der globalen Liste hinzu
        return True
    return False


def get_commit_type(message):
    """
    Extrahiert den Commit-Typ (wie 'feat', 'fix', etc.) oder einen benutzerdefinierten Typ aus einer Commit-Nachricht.

    Args:
        message (str): Die Commit-Nachricht.

    Returns:
        str: Der Commit-Typ (z.B. 'feat', 'fix' oder 'custom-feature'), falls vorhanden.
        None: Falls kein Commit-Typ gefunden wird.
    """
    pattern = r"^([a-zA-Z]+)(?:\([\w\-\.\s]+\))?!?: .+"
    match = re.match(pattern, message.lower())
    if match:
        return match.group(1)  # Typ wie 'feat', 'fix', oder 'custom-feature'
    return None


def find_80_percent_conventional_date(json_file_path, min_cc_percentage=0.8, min_cc_commits=10):
    """
    Findet das Datum, ab dem mindestens 80 % der Commits, die ab diesem Zeitpunkt gemacht wurden, "conventional" sind.

    Args:
        json_file_path (str): Pfad zur JSON-Datei, die die Commits und die Analyse enthält.

    Returns:
        str: Das Datum im Format 'YYYY-MM-DD', ab dem 80 % der Commits konventionell sind.
    """
    # JSON-Datei laden
    data = load_json(json_file_path)

    # Extrahiere die Commits
    commits = data.get("commits", [])

    # Extrahiere die Anzahl der Commits aus der analysis_summary
    total_commits = data.get("analysis_summary", {}).get("total_commits", 0)
    if total_commits == 0:
        return "Keine Commits verfügbar"

    total_conventional_commits = data.get("analysis_summary", {}).get("conventional_commits", 0)
    if total_conventional_commits < min_cc_commits:
        return "Summe der CC kleiner als 10"

    # Umkehren der Commit-Liste, sodass der älteste Commit an Index 0 steht
    commits_reversed = commits[::-1]

    # Kumulative Summe der konventionellen Commits berechnen
    cum_conventional_commits = [0] * (total_commits + 1)
    for i in range(1, total_commits + 1):
        is_conv = 1 if commits_reversed[i - 1].get("is_conventional") else 0
        cum_conventional_commits[i] = cum_conventional_commits[i - 1] + is_conv

    # Minimale Anzahl verbleibender Commits berechnen
    min_remaining_commits = int(math.ceil(min_cc_commits / min_cc_percentage))

    # Iterieren über die Commits
    for i in range(total_commits):
        num_remaining_commits = total_commits - i
        if num_remaining_commits < min_remaining_commits:
            break  # Nicht genug verbleibende Commits
        conventional_commits = cum_conventional_commits[total_commits] - cum_conventional_commits[i]
        cc_percentage = conventional_commits / num_remaining_commits

        if cc_percentage >= min_cc_percentage and conventional_commits >= min_cc_commits:
            return commits_reversed[i]['committed_datetime'][:10]  # Rückgabe des Datums ab diesem Commit

    return "Nicht genug konventionelle Commits gefunden"


def calculate_monthly_conventional_commits(json_file_path):
    """
    Berechnet den prozentualen Anteil der konventionellen Commits mit cc_type und custom_type für jeden Monat.

    Args:
        json_file_path (str): Pfad zur JSON-Datei.

    Returns:
        dict: Zwei Dictionaries:
              - Anteil der Commits mit cc_type pro Monat
              - Anteil der Commits mit custom_type pro Monat
    """
    # JSON-Daten laden
    data = load_json(json_file_path)

    # Extrahiere die Commits
    commits = data.get("commits", [])

    # Dictionary, um die Anzahl der Commits pro Monat zu speichern
    monthly_commits = defaultdict(
        lambda: {"total": 0, "conventional_with_cc_type": 0, "conventional_with_custom_type": 0})

    # Commits nach Monat gruppieren und konventionelle Commits mit cc_type und custom_type zählen
    for commit in commits:
        commit_date_str = commit.get("committed_datetime")
        cc_type = commit.get("cc_types", None)
        custom_type = commit.get("custom_types", None)

        commit_date = datetime.fromisoformat(commit_date_str)
        year_month = commit_date.strftime("%Y-%m")

        # Zähle den Commit für den jeweiligen Monat
        monthly_commits[year_month]["total"] += 1
        if cc_type:
            monthly_commits[year_month]["conventional_with_cc_type"] += 1
        if custom_type:
            monthly_commits[year_month]["conventional_with_custom_type"] += 1

    # Berechne den prozentualen Anteil pro Monat für cc_type und custom_type
    monthly_cc_type_percentage = {
        month: (data["conventional_with_cc_type"] / data["total"]) * 100 if data["total"] > 0 else 0
        for month, data in monthly_commits.items()
    }

    monthly_custom_type_percentage = {
        month: (data["conventional_with_custom_type"] / data["total"]) * 100 if data["total"] > 0 else 0
        for month, data in monthly_commits.items()
    }

    return monthly_cc_type_percentage, monthly_custom_type_percentage

