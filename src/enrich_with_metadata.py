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
    total_commits = len(commits)
    conventional_commits = 0
    unconventional_commits = 0
    cc_type_commits = 0
    custom_type_commits = 0

    all_custom_type_counter = Counter()
    all_cc_type_counter = Counter()

    cc_types = ["feat", "fix", "docs", "style", "refactor", "perf",
                "test", "build", "ci", "chore", "revert"]

    # Erster Durchlauf: Sammle alle Custom Types und CC Types
    for commit in commits:
        message = commit.get("message", "")
        commit_type = get_commit_type(message)
        if commit_type:
            if is_conventional_commit(message):
                all_cc_type_counter[commit_type] += 1
            elif is_conventional_custom(message):
                all_custom_type_counter[commit_type] += 1

    # Identifiziere konsistente Custom Types
    consistent_custom_types = identify_consistent_custom_types(all_custom_type_counter, total_commits)

    # Re-Initialisiere die Counter für den zweiten Durchlauf
    cc_type_counter = Counter()
    custom_type_counter = Counter()

    # Zweiter Durchlauf: Markiere Commits entsprechend und aktualisiere Zähler
    for commit in commits:
        message = commit.get("message", "")
        commit_type = get_commit_type(message)
        if commit_type:
            if is_conventional_commit(message):
                # Standard CC Commit
                enriched_commit = {
                    **commit,
                    'is_conventional': True,
                    'cc_type': commit_type,
                    'custom_type': None
                }
                conventional_commits += 1
                cc_type_commits += 1
                cc_type_counter[commit_type] += 1
            elif is_conventional_custom(message) and commit_type in consistent_custom_types:
                # Konsistenter Custom Type
                enriched_commit = {
                    **commit,
                    'is_conventional': True,
                    'cc_type': None,
                    'custom_type': commit_type
                }
                conventional_commits += 1
                custom_type_commits += 1
                custom_type_counter[commit_type] += 1
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
            # Unkonventioneller Commit (kein Typ erkannt)
            enriched_commit = {
                **commit,
                'is_conventional': False,
                'cc_type': None,
                'custom_type': None
            }
            unconventional_commits += 1

        enriched_commits.append(enriched_commit)

    # Erstelle die Zusammenfassung
    summary = {
        'total_commits': total_commits,
        'conventional_commits': conventional_commits,
        'unconventional_commits': unconventional_commits,
        'cc_type_commits': cc_type_commits,
        'custom_type_commits': custom_type_commits,
        'custom_type_distribution': dict(custom_type_counter),
        'cc_type_distribution': dict(cc_type_counter),
    }

    # Überprüfe, ob cc_type_commits > 200
    if cc_type_commits > 200:
        # Berechne das CC-Einführungsdatum
        cc_adoption_date = find_80_percent_conventional_date(
            enriched_commits,
            min_cc_percentage=0.6,
            min_cc_commits=10
        )
        summary['cc_adoption_date'] = cc_adoption_date
        if cc_adoption_date is not None:
            print(f"\n CC-Einführungsdatum: {cc_adoption_date}\n")
    else:
        # Setze das CC-Einführungsdatum auf None
        summary['cc_adoption_date'] = None
        print(
            "Zu wenige Commits mit CC-Typen ")

    return enriched_commits, summary
