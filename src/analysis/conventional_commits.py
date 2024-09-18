import re
from conventional_pre_commit.format import is_conventional

# Globale Liste zum Speichern der benutzerdefinierten Typen
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
