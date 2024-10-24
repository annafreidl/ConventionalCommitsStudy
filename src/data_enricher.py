# data_enricher.py
import logging
import re
from collections import Counter
from typing import List, Dict, Tuple, Any

from data_enricher import *
from analyzer import find_cc_adoption_date
from testing import binary_segmentation_date_analysis


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


def enrich_commits(commits: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Reicht die Commits mit Metadaten an und erstellt eine Zusammenfassung.

    Args:
        commits (List[Dict[str, Any]]): Liste von Commits.

    Returns:
        Tuple[List[Dict[str, Any]], Dict[str, Any]]: Eine Liste der angereicherten Commits und eine Zusammenfassung.
    """
    logger = logging.getLogger(__name__)

    total_commits = len(commits)
    cc_type_commits = 0

    cc_type_counter = Counter()
    all_custom_type_counter = Counter()

    enriched_commits = []

    logger.debug(f"Starte Anreicherung von {total_commits} Commits.")

    for commit in commits:
        message = commit.get("message", "")
        commit_type = get_commit_type(message)

        is_cc = is_conventional_commit(message)
        is_custom = is_conventional_custom(message)

        enriched_commit = {
            **commit,
            'is_conventional': False,
            'cc_type': None,
            'custom_type': None
        }

        if commit_type:
            if is_cc:
                enriched_commit['is_conventional'] = True
                enriched_commit['cc_type'] = commit_type
                cc_type_commits += 1
                cc_type_counter[commit_type] += 1
            elif is_custom:
                enriched_commit['is_conventional'] = True
                enriched_commit['custom_type'] = commit_type
                all_custom_type_counter[commit_type] += 1
            # Sonst wird der Commit als unkonventionell betrachtet
        # Wenn kein Commit-Typ vorhanden ist, wird der Commit als unkonventionell betrachtet

        enriched_commits.append(enriched_commit)

    # Identifizieren der konsistenten Custom-Typen basierend auf dem Schwellenwert
    consistent_custom_types = identify_consistent_custom_types(all_custom_type_counter, total_commits)
    logger.debug(f"Konsistente Custom-Typen identifiziert: {consistent_custom_types}")

    # Aktualisieren der angereicherten Commits, um inkonsistente Custom-Typen herauszufiltern
    for commit in enriched_commits:
        if commit['custom_type'] and commit['custom_type'] not in consistent_custom_types:
            commit['is_conventional'] = False
            commit['custom_type'] = None

    # Neu Berechnen der Zähler basierend auf den aktualisierten Commits
    conventional_commits = 0
    unconventional_commits = 0
    custom_type_commits = 0
    custom_type_counter = Counter()

    for commit in enriched_commits:
        if commit['is_conventional']:
            conventional_commits += 1
            if commit['custom_type']:
                custom_type_commits += 1
                custom_type_counter[commit['custom_type']] += 1
        else:
            unconventional_commits += 1

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

    if should_analyze_cc_adoption(summary):
        logger.info("Analysiere CC-Einführungsdatum.")
        cc_adoption_date = binary_segmentation_date_analysis(enriched_commits, summary)
        summary['cc_adoption_date'] = cc_adoption_date
    else:
        logger.info("Analyse des CC-Einführungsdatums nicht erforderlich.")

    return enriched_commits, summary
