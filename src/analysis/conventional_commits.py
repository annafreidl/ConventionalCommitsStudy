import re
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


def find_80_percent_conventional_date(json_file_path):
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

    # Rückwärts durch die Commits gehen (von den ältesten zu den neuesten)
    for i in range(total_commits - 1, -1, -1):
        # Betrachte die verbleibenden Commits ab diesem Zeitpunkt
        remaining_commits = total_commits - i  # Korrektur hier: verbleibende Commits ab diesem Index
        remaining_commit_list = commits[0:i]  # Die Liste der verbleibenden Commits ab diesem Commit

        # Zähle die konventionellen Commits unter den verbleibenden Commits
        conventional_commits = sum(1 for commit in remaining_commit_list if commit.get("is_conventional"))

        # Debugging: Ausgabe, um zu sehen, wie viele konventionelle und verbleibende Commits es gibt
        # print(f"Ab Commit {i}: {conventional_commits}/{i} sind konventionell")

        # Berechne den Anteil der konventionellen Commits
        if remaining_commits > 0 and (conventional_commits / (i+1)) >= 0.8:
            return commits[i]['committed_datetime']  # Rückgabe des frühesten Datums

    return "Nicht genug konventionelle Commits gefunden"
