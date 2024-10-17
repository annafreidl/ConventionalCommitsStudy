# data_enricher.py
import re
from collections import Counter
from data_enricher import *
from analyzer import find_cc_adoption_date


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


def should_analyze_cc_adoption(analysis_summary):
    total_commits = analysis_summary.get("total_commits", 0)
    cc_type_commits = analysis_summary.get("cc_type_commits", 0)

    if total_commits == 0:
        return False

    cc_rate = cc_type_commits / total_commits

    if cc_rate >= 0.10 and cc_type_commits >= 500:
        return True
    else:
        return False


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
        'cc_adoption_date': None
    }

    # if cc_type_commits > 200:
    #     cc_adoption_date = find_cc_adoption_date(
    #         enriched_commits,
    #         min_cc_percentage=0.6,
    #         min_cc_commits=10
    #     )
    #     summary['cc_adoption_date'] = cc_adoption_date
    # else:
    #     summary['cc_adoption_date'] = None

    return enriched_commits, summary



