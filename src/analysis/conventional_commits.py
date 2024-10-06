import math
import re
from collections import defaultdict
from datetime import datetime

def parse_commit_message(message):
    """
    Parst eine Commit-Nachricht und gibt den Typ, Scope, Breaking-Change-Indikator und Beschreibung zurück.
    """
    pattern = r"^([a-zA-Z]+)(?:\(([\w\-\.\s]+)\))?(!)?: (.+)"
    match = re.match(pattern, message.lower())
    if match:
        commit_type = match.group(1)
        scope = match.group(2)
        if scope:
            scope = scope.strip()
        breaking = match.group(3) == '!'
        description = match.group(4)
        return {'type': commit_type, 'scope': scope, 'breaking': breaking, 'description': description}
    return None

def is_conventional_commit(commit_message):
    """
    Prüft, ob eine Commit-Nachricht der CC-Convention entspricht.
    """
    cc_types = ["feat", "fix", "docs", "style", "refactor", "perf",
                "test", "build", "ci", "chore", "revert"]
    parsed = parse_commit_message(commit_message)
    if parsed and parsed['type'] in cc_types:
        return True
    return False



def is_conventional_custom(commit_message):
    """
    Prüft, ob eine Commit-Nachricht der CC-Convention mit custom Typen entspricht.
    """
    cc_types = ["feat", "fix", "docs", "style", "refactor", "perf",
                "test", "build", "ci", "chore", "revert"]
    parsed = parse_commit_message(commit_message)
    if parsed and parsed['type'] not in cc_types:
        return True
    return False



def get_commit_type(message):
    """
    Extrahiert den Commit-Typ aus einer Commit-Nachricht.
    """
    parsed = parse_commit_message(message)
    if parsed:
        return parsed['type']
    return None



def find_80_percent_conventional_date(commits, min_cc_percentage=0.8, min_cc_commits=10):

    total_commits = len(commits)
    if total_commits == 0:
        return None  # Keine Commits verfügbar
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

        # Überprüfe, ob genügend verbleibende Commits vorhanden sind
        if num_remaining_commits < min_remaining_commits:
            break  # Nicht genug verbleibende Commits

        conventional_commits = cum_conventional_commits[total_commits] - cum_conventional_commits[i]
        cc_percentage = conventional_commits / num_remaining_commits

        # Überprüfe, ob sowohl der Mindestprozentsatz als auch die Mindestanzahl an konventionellen Commits erreicht sind
        if cc_percentage >= min_cc_percentage and conventional_commits >= min_cc_commits:
            return commits_reversed[i]['committed_datetime'][:10]  # Rückgabe des Datums ab diesem Commit

    return None  # Nicht genug konventionelle Commits gefunden


def calculate_monthly_conventional_commits(commits):
    """
    Berechnet den prozentualen Anteil der konventionellen Commits mit cc_type und custom_type für jeden Monat.

    Args:
        commits (list): Liste der angereicherten Commits.

    Returns:
        tuple: Zwei Dictionaries:
              - Anteil der Commits mit cc_type pro Monat
              - Anteil der Commits mit custom_type pro Monat
    """
    # Dictionary, um die Anzahl der Commits pro Monat zu speichern
    monthly_commits = defaultdict(
        lambda: {"total": 0, "conventional_with_cc_type": 0, "conventional_with_custom_type": 0})

    # Commits nach Monat gruppieren und konventionelle Commits mit cc_type und custom_type zählen
    for commit in commits:
        commit_date_str = commit.get("committed_datetime")
        cc_type = commit.get("cc_type", None)
        custom_type = commit.get("custom_type", None)

        # Sicherstellen, dass commit_date_str nicht None ist
        if not commit_date_str:
            continue  # Überspringe Commits ohne Datum

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
        month: (counts["conventional_with_cc_type"] / counts["total"]) * 100 if counts["total"] > 0 else 0
        for month, counts in monthly_commits.items()
    }

    monthly_custom_type_percentage = {
        month: (counts["conventional_with_custom_type"] / counts["total"]) * 100 if counts["total"] > 0 else 0
        for month, counts in monthly_commits.items()
    }

    return monthly_cc_type_percentage, monthly_custom_type_percentage
