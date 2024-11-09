# Standard library imports
import logging
import re
from collections import Counter
from typing import List, Dict, Tuple, Any

# Local module imports
from change_point_detection import binary_segmentation_date_analysis


def identify_consistent_custom_types(custom_type_counter, total_commits, min_absolute=3, min_percentage=0.00):
    """
    Identifies consistent custom types based on their frequency.

    Args:
        custom_type_counter (Counter): Counter with the frequency of custom types.
        total_commits (int): Total number of commits.
        min_absolute (int): Minimum absolute frequency (default: 3).
        min_percentage (float): Minimum percentage frequency (default: 0.00).

    Returns:
        set: Set of consistent custom types.
    """
    consistent_custom_types = set()
    for custom_type, count in custom_type_counter.items():
        percentage = (count / total_commits) * 100
        if count >= min_absolute and percentage >= min_percentage:
            consistent_custom_types.add(custom_type)
    return consistent_custom_types


def parse_commit_message(message):
    """
    Parses a commit message and returns its type, scope, breaking-change indicator, and description.
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
    Checks if a commit message conforms to the Conventional Commit (CC) standard.
    """
    cc_types = ["feat", "fix", "docs", "style", "refactor", "perf",
                "test", "build", "ci", "chore", "revert"]
    parsed = parse_commit_message(commit_message)
    if parsed and parsed['type'] in cc_types:
        return True
    return False


def is_conventional_custom(commit_message):
    """
    Checks if a commit message conforms to the CC standard but uses custom types.
    """
    cc_types = ["feat", "fix", "docs", "style", "refactor", "perf",
                "test", "build", "ci", "chore", "revert"]
    parsed = parse_commit_message(commit_message)
    if parsed and parsed['type'] not in cc_types:
        return True
    return False


def get_commit_type(message):
    """
    Extracts the commit type from a commit message.
    """
    parsed = parse_commit_message(message)
    if parsed:
        return parsed['type']
    return None


def should_analyze_cc_adoption(analysis_summary):
    """
    Determines whether the CC adoption date should be analyzed based on summary data.
    """
    total_commits = analysis_summary.get("total_commits", 0)
    cc_type_commits = analysis_summary.get("cc_type_commits", 0)

    if total_commits == 0:
        return False

    cc_rate = cc_type_commits / total_commits

    return cc_rate >= 0.10 or cc_type_commits >= 500


def enrich_commits(
        commits: List[Dict[str, Any]], summary: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Enriches commits with metadata and creates a summary of the data.

    Args:
        commits (List[Dict[str, Any]]): List of commits.
        summary (Dict[str, Any]): Summary dictionary to be updated.

    Returns:
        Tuple[List[Dict[str, Any]], Dict[str, Any]]: A list of enriched commits and an updated summary.
    """
    logger = logging.getLogger(__name__)

    total_commits = len(commits)
    cc_type_commits = 0
    custom_type_commits = 0

    cc_type_counter = Counter()
    custom_type_counter = Counter()

    enriched_commits = []

    logging.info(f"Starting enrichment of {total_commits} commits.")

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
                custom_type_commits += 1
                custom_type_counter[commit_type] += 1
            # Otherwise, the commit is considered unconventional

        enriched_commits.append(enriched_commit)

    conventional_commits = cc_type_commits + custom_type_commits
    unconventional_commits = total_commits - conventional_commits

    # Calculate the overall CC adoption rate
    overall_cc_adoption_rate = (cc_type_commits / total_commits) * 100 if total_commits > 0 else 0

    summary = {
        **summary,
        'total_commits': total_commits,
        'conventional_commits': conventional_commits,
        'unconventional_commits': unconventional_commits,
        'cc_type_commits': cc_type_commits,
        'custom_type_commits': custom_type_commits,
        'custom_type_distribution': dict(custom_type_counter),
        'cc_type_distribution': dict(cc_type_counter),
        'overall_cc_adoption_rate': round(overall_cc_adoption_rate),
        'cc_adoption_date': None,
        'is_consistently_conventional': False
    }

    # Determine if the repository is consistently conventional based on the overall adoption rate
    if overall_cc_adoption_rate >= 80:
        logger.info("Repository is consistently conventional.")
        summary['is_consistently_conventional'] = True
        summary['cc_adoption_date'] = summary.get('created_at')
    elif should_analyze_cc_adoption(summary):
        logger.info("Analyzing CC adoption date.")
        cc_adoption_date = binary_segmentation_date_analysis(enriched_commits)
        summary['cc_adoption_date'] = cc_adoption_date
    else:
        logger.info("Criteria for CC adoption date analysis not met.")

    return enriched_commits, summary
