from analysis import is_conventional_commit, is_conventional_custom, get_commit_type


def enrich_commits_with_metadata(commits):
    """
    Fügt jedem Commit die Felder 'is_conventional', 'cc_type' oder 'custom_type' hinzu.
    """
    enriched_commits = []
    for commit in commits:
        message = commit.get("message", "")

        # Prüfe, ob es ein konventioneller Commit nach der CC-Spezifikation ist
        if is_conventional_commit(message):
            enriched_commits.append({
                **commit,
                "is_conventional": True,
                "cc_type": get_commit_type(message),
                "custom_type": None
            })
        # Prüfe, ob es ein benutzerdefinierter konventioneller Commit ist
        elif is_conventional_custom(message):
            enriched_commits.append({
                **commit,
                "is_conventional": True,
                "cc_type": None,
                "custom_type": get_commit_type(message)
            })
        # Kein konventioneller Commit
        else:
            enriched_commits.append({
                **commit,
                "is_conventional": False,
                "cc_type": None,
                "custom_type": None
            })

    return enriched_commits
