from analysis import is_conventional_commit, is_conventional_custom, get_commit_type
from collections import Counter
from constants import *


def enrich_commits_with_metadata(commits):
    """
    Fügt jedem Commit die Felder 'is_conventional', 'cc_type' oder 'custom_type' hinzu.
    Erstellt währenddessen eine Zusammenfassung der Analyse.
    """
    enriched_commits = []

    # Initialisiere Zähler und Counter für die Zusammenfassung
    total_commits = 0
    conventional_commits = 0
    unconventional_commits = 0
    custom_type_counter = Counter()
    cc_type_counter = Counter()

    for commit in commits:
        total_commits += 1
        message = commit.get("message", "")

        # Prüfe, ob es ein konventioneller Commit nach der CC-Spezifikation ist
        if is_conventional_commit(message):
            cc_type = get_commit_type(message)
            enriched_commit = {
                **commit,
                KEY_IS_CONVENTIONAL: True,
                KEY_CC_TYPES: cc_type,
                KEY_CUSTOM_TYPES: None
            }
            conventional_commits += 1
            if cc_type:
                cc_type_counter[cc_type] += 1
        # Prüfe, ob es ein benutzerdefinierter konventioneller Commit ist
        elif is_conventional_custom(message):
            custom_type = get_commit_type(message)
            enriched_commit = {
                **commit,
                KEY_IS_CONVENTIONAL: True,
                KEY_CC_TYPES: None,
                KEY_CUSTOM_TYPES: custom_type
            }
            conventional_commits += 1
            if custom_type:
                custom_type_counter[custom_type] += 1
        # Kein konventioneller Commit
        else:
            enriched_commit = {
                **commit,
                KEY_IS_CONVENTIONAL: False,
                KEY_CC_TYPES: None,
                KEY_CUSTOM_TYPES: None
            }
            unconventional_commits += 1

        enriched_commits.append(enriched_commit)

    # Erstelle die Zusammenfassung
    summary = {
        TOTAL_COMMITS_KEY: total_commits,
        CONVENTIONAL_COMMITS_KEY: conventional_commits,
        UNCONVENTIONAL_COMMITS_KEY: unconventional_commits,
        CUSTOM_TYPE_DISTRIBUTION_KEY: dict(custom_type_counter),
        CC_TYPE_DISTRIBUTION_KEY: dict(cc_type_counter)
    }

    return enriched_commits, summary
