from constants import COMMIT_ANALYSIS_RESULTS
from repository_manager import clone_repository
from commit_loader import load_commits
from data_enricher import enrich_commits
from data_saver import save_to_json, load_from_json
from analyzer import search_for_cc_indications
from typing import Dict, Any
import logging
from datetime import datetime


def convert_date_format(original_date_str):
    """
    Converts a date from ISO 8601 format to 'YYYY-MM-DD' format.

    :param original_date_str: The original date in ISO 8601 format.
    :return: The converted date in 'YYYY-MM-DD' format.
    """
    # Convert the date
    date_object = datetime.fromisoformat(original_date_str[:-1])  # Remove the 'Z' at the end
    formatted_date = date_object.strftime('%Y-%m-%d')
    return formatted_date


def process_repository(repo_data: Dict[str, Any]) -> None:
    """
    Processes a repository by loading, analyzing, and classifying its data.

    Steps:
    1. Extracts metadata from repo_data.
    2. Clones or loads the repository.
    3. Loads or creates commit data.
    4. Analyze commits for the adoption of Conventional Commits.
    5. Searches for indications of Conventional Commits usage.

    Args:
        repo_data (Dict[str, Any]): The metadata of the repository.
    """
    repo_name = repo_data.get("name", "Unknown").replace("/", "_")
    language = repo_data.get("language", "Unknown")
    size = repo_data.get("size", 0)
    repo_id = repo_data.get("id", 0)
    owner = repo_data.get("owner", {})
    created_at = convert_date_format(repo_data.get("created_at", ""))
    homepage = repo_data.get("homepage")

    json_file_path = COMMIT_ANALYSIS_RESULTS / f"{repo_id}.json"

    logging.info(f"Processing repository {repo_name}...")

    if json_file_path.exists():
        return

    logging.info(f"Cloning repository {repo_name}..., {json_file_path} hat nicht existiert")
    # Try to load or clone the repository
    repo = clone_repository(repo_data)
    if not repo:
        logging.warning(f"Could not clone or load repository {repo_name}.")
        return

    # Search for indications of Conventional Commits usage
    using_cc = search_for_cc_indications(repo, homepage)

    logging.info(f"Loading and analyzing commits for {repo_name}...")
    commits = load_commits(repo)
    summary = {
        "language": language,
        "size": size,
        "id": repo_id,
        "owner": owner,
        "created_at": created_at,
        "cc_adoption_date": None,
        "name": repo_name,
        "overall_cc_adoption_rate": 0,
        "is_consistently_conventional": False,
        "cc_indication": using_cc,
    }

    # Add additional metadata to the summary
    enriched_commits, enriched_summary = enrich_commits(commits, summary)

    # Save the data for further analysis
    save_to_json(enriched_commits, enriched_summary, json_file_path)


# def process_repository(repo_data: Dict[str, Any]) -> None:
#     """
#     Processes a repository by loading, analyzing, and classifying its data.
#
#     Steps:
#     1. Extracts metadata from repo_data.
#     2. Clones or loads the repository.
#     3. Loads or creates commit data.
#     4. Analyze commits for the adoption of Conventional Commits.
#     5. Searches for indications of Conventional Commits usage.
#
#     Args:
#         repo_data (Dict[str, Any]): The metadata of the repository.
#     """
#     repo_name = repo_data.get("name", "Unknown").replace("/", "_")
#     language = repo_data.get("language", "Unknown")
#     size = repo_data.get("size", 0)
#     repo_id = repo_data.get("id", 0)
#     owner = repo_data.get("owner", {})
#     created_at = convert_date_format(repo_data.get("created_at", ""))
#     homepage = repo_data.get("homepage")
#
#     json_file_path = RESULTS / f"{repo_id}.json"
#
#     logging.info(f"Processing repository {repo_name}...")
#
#     if json_file_path.exists():
#         return
#
#     # Try to load or clone the repository
#     repo = clone_repository(repo_data)
#     if not repo:
#         logging.warning(f"Could not clone or load repository {repo_name}.")
#         return
#
#     # Search for indications of Conventional Commits usage
#     using_cc = search_for_cc_indications(repo, homepage)
#
#     logging.info(f"Loading and analyzing commits for {repo_name}...")
#     commits = load_commits(repo)
#     summary = {
#         "language": language,
#         "size": size,
#         "id": repo_id,
#         "owner": owner,
#         "created_at": created_at,
#         "cc_adoption_date": None,
#         "name": repo_name,
#         "overall_cc_adoption_rate": 0,
#         "is_consistently_conventional": False,
#         "cc_indication": using_cc,
#     }
#
#     # Add additional metadata to the summary
#     enriched_commits, enriched_summary = enrich_commits(commits, summary)
#
#     # Save the data for further analysis
#     save_to_json(enriched_commits, enriched_summary, json_file_path)
