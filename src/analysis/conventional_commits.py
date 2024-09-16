import re
from conventional_pre_commit.format import is_conventional

# Globale Liste zum Speichern der benutzerdefinierten Typen
custom_types = []


def is_conventional_commit(commit_message):
    """
    Prüft, ob eine Commit-Nachricht der Conventional Commits-Konvention entspricht.
    """

    # wichtig, dass die Nachricht in Kleinbuchstaben umgewandelt wird,
    # damit alle Typen mit is_conventional gefunden werden
    commit_message = commit_message.lower()

    # Unterscheidung zwischen custom und CC
    if is_conventional(commit_message):
        return True
    elif is_conventional_custom(commit_message):
        return True
    else:
        return False


def is_conventional_custom(commit_message):
    pattern = r"^([a-zA-Z]+)(?:\(([\w\-\.\s]+)\))?!?: .+"

    match = re.match(pattern, commit_message)
    if match:
        custom_type = match.group(1)
        custom_types.append(custom_type)
        return True
    else:
        return False
