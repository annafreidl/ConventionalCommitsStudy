from analysis import is_conventional_commit, is_conventional_custom, get_commit_type, find_80_percent_conventional_date
from collections import Counter


def identify_consistent_custom_types(custom_type_counter, total_commits, min_absolute=3, min_percentage=0.00):
    """
    Identifiziert konsistente Custom Types basierend auf ihrer Häufigkeit.

    Args:
        custom_type_counter (Counter): Counter mit der Häufigkeit der Custom Types.
        total_commits (int): Gesamtzahl der Commits.
        min_absolute (int): Minimale absolute Häufigkeit. Hier 3
        min_percentage (float): Minimale prozentuale Häufigkeit (zwischen 0 und 100).

    Returns:
        set: Menge der konsistenten Custom Types.
    """
    consistent_custom_types = set()
    for custom_type, count in custom_type_counter.items():
        percentage = (count / total_commits) * 100
        if count >= min_absolute and percentage >= min_percentage:
            consistent_custom_types.add(custom_type)
    return consistent_custom_types


def enrich_commits_with_metadata(commits):
    enriched_commits = []

    # Initialisiere Zähler und Counter für die Zusammenfassung
    total_commits = 0
    conventional_commits = 0
    unconventional_commits = 0
    cc_type_counter = Counter()
    # Temporärer Counter für alle Custom Types
    all_custom_type_counter = Counter()

    # Erster Durchlauf: Sammle alle Custom Types
    for commit in commits:
        total_commits += 1
        message = commit.get("message", "")

        # Prüfe, ob es ein Standard-CC-Commit ist
        if is_conventional_commit(message):
            cc_type = get_commit_type(message)
            if cc_type:
                cc_type_counter[cc_type] += 1
        # Prüfe, ob es ein benutzerdefinierter Commit ist
        elif is_conventional_custom(message):
            custom_type = get_commit_type(message)
            if custom_type:
                all_custom_type_counter[custom_type] += 1

    # Identifiziere konsistente Custom Types
    consistent_custom_types = identify_consistent_custom_types(all_custom_type_counter, total_commits)

    # Initialisiere den custom_type_counter neu für die konsistenten Custom Types
    custom_type_counter = Counter()

    # Zweiter Durchlauf: Markiere Commits entsprechend und aktualisiere Zähler
    for commit in commits:
        message = commit.get("message", "")

        # Prüfe, ob es ein Standard-CC-Commit ist
        if is_conventional_commit(message):
            cc_type = get_commit_type(message)
            enriched_commit = {
                **commit,
                'is_conventional': True,
                'cc_type': cc_type,
                'custom_type': None
            }
            conventional_commits += 1
            if cc_type:
                cc_type_counter[cc_type] += 1  # Zähler aktualisieren
        # Prüfe, ob es ein konsistenter Custom Type ist
        elif is_conventional_custom(message):
            custom_type = get_commit_type(message)
            if custom_type in consistent_custom_types:
                enriched_commit = {
                    **commit,
                    'is_conventional': True,
                    'cc_type': None,
                    'custom_type': custom_type
                }
                conventional_commits += 1
                custom_type_counter[custom_type] += 1  # Nur konsistente Custom Types zählen
            else:
                # Unkonventioneller Commit
                enriched_commit = {
                    **commit,
                    'is_conventional': False,
                    'cc_type': None,
                    'custom_type': None
                }
                unconventional_commits += 1
        else:
            # Unkonventioneller Commit
            enriched_commit = {
                **commit,
                'is_conventional': False,
                'cc_type': None,
                'custom_type': None
            }
            unconventional_commits += 1

        enriched_commits.append(enriched_commit)

    # **Compute the CC adoption date**
    cc_adoption_date = find_80_percent_conventional_date(
        enriched_commits,
        min_cc_percentage=0.8,
        min_cc_commits=10
    )

    # Erstelle die Zusammenfassung
    summary = {
        'total_commits': total_commits,
        'conventional_commits': conventional_commits,
        'unconventional_commits': unconventional_commits,
        'custom_type_distribution': dict(custom_type_counter),
        'cc_type_distribution': dict(cc_type_counter),
        'cc_adoption_date': cc_adoption_date  # Add the date to the summary
    }

    return enriched_commits, summary
