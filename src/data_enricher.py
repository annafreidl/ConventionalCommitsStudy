# data_enricher.py

from collections import Counter
from analysis import (
    is_conventional_commit,
    is_conventional_custom,
    get_commit_type,
    find_80_percent_conventional_date
)


def identify_consistent_custom_types(custom_type_counter, total_commits, min_absolute=3):
    """
    Identifiziert konsistente Custom Types.

    Args:
        custom_type_counter (Counter): Zähler für Custom Types.
        total_commits (int): Gesamtzahl der Commits.

    Returns:
        set: Set von konsistenten Custom Types.
    """
    return {ctype for ctype, count in custom_type_counter.items() if count >= min_absolute}


def enrich_commits(commits):
    """
    Reicht die Commits mit Metadaten an und erstellt eine Zusammenfassung.

    Args:
        commits (list): Liste von Commits.

    Returns:
        tuple: (enriched_commits, summary)
    """
    enriched_commits = []
    total_commits = len(commits)
    conventional_commits = 0
    unconventional_commits = 0
    cc_type_commits = 0
    custom_type_commits = 0

    all_custom_type_counter = Counter()
    all_cc_type_counter = Counter()

    cc_types = ["feat", "fix", "docs", "style", "refactor", "perf",
                "test", "build", "ci", "chore", "revert"]

    for commit in commits:
        message = commit.get("message", "")
        commit_type = get_commit_type(message)
        if commit_type:
            if is_conventional_commit(message):
                all_cc_type_counter[commit_type] += 1
            elif is_conventional_custom(message):
                all_custom_type_counter[commit_type] += 1

    consistent_custom_types = identify_consistent_custom_types(all_custom_type_counter, total_commits)

    cc_type_counter = Counter()
    custom_type_counter = Counter()

    for commit in commits:
        message = commit.get("message", "")
        commit_type = get_commit_type(message)
        if commit_type:
            if is_conventional_commit(message):
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
                enriched_commit = {
                    **commit,
                    'is_conventional': False,
                    'cc_type': None,
                    'custom_type': None
                }
                unconventional_commits += 1
        else:
            enriched_commit = {
                **commit,
                'is_conventional': False,
                'cc_type': None,
                'custom_type': None
            }
            unconventional_commits += 1

        enriched_commits.append(enriched_commit)

    summary = {
        'total_commits': total_commits,
        'conventional_commits': conventional_commits,
        'unconventional_commits': unconventional_commits,
        'cc_type_commits': cc_type_commits,
        'custom_type_commits': custom_type_commits,
        'custom_type_distribution': dict(custom_type_counter),
        'cc_type_distribution': dict(cc_type_counter),
    }

    if cc_type_commits > 200:
        cc_adoption_date = find_80_percent_conventional_date(
            enriched_commits,
            min_cc_percentage=0.6,
            min_cc_commits=10
        )
        summary['cc_adoption_date'] = cc_adoption_date
    else:
        summary['cc_adoption_date'] = None

    return enriched_commits, summary
