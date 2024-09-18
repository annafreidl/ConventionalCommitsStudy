from analysis import is_conventional_commit, is_conventional_custom, get_commit_type


from collections import Counter

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
                "is_conventional": True,
                "cc_type": cc_type,
                "custom_type": None
            }
            conventional_commits += 1
            if cc_type:
                cc_type_counter[cc_type] += 1
        # Prüfe, ob es ein benutzerdefinierter konventioneller Commit ist
        elif is_conventional_custom(message):
            custom_type = get_commit_type(message)
            enriched_commit = {
                **commit,
                "is_conventional": True,
                "cc_type": None,
                "custom_type": custom_type
            }
            conventional_commits += 1
            if custom_type:
                custom_type_counter[custom_type] += 1
        # Kein konventioneller Commit
        else:
            enriched_commit = {
                **commit,
                "is_conventional": False,
                "cc_type": None,
                "custom_type": None
            }
            unconventional_commits += 1

        enriched_commits.append(enriched_commit)

    # Erstelle die Zusammenfassung
    summary = {
        "total_commits": total_commits,
        "conventional_commits": conventional_commits,
        "unconventional_commits": unconventional_commits,
        "custom_type_distribution": dict(custom_type_counter),
        "cc_type_distribution": dict(cc_type_counter)
    }

    return enriched_commits, summary
