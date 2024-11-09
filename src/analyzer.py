# Standard library imports
import logging
import os
import re
import json
import requests

from pathlib import Path
from bs4 import BeautifulSoup


def check_homepage_for_cc(homepage_url):
    """
    Searches the repository's homepage for indications of adherence to the Conventional Commit (CC) convention.

    Args:
        homepage_url (str): URL of the repository's homepage.

    Returns:
        bool: True if indications are found, False otherwise.
    """
    keywords = [
        "Conventional Commits",
        "Conventional Commit",
        "conventionalcommits.org",
        "Conventional Changelog",
        "Commit Message Convention",
        "Commit Guidelines",
        "commitizen",
        "commitlint",
        "standard-version",
        "semantic-release"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CCChecker/1.0)"
    }

    try:
        response = requests.get(homepage_url, headers=headers, timeout=10)
        response.raise_for_status()  # Check for HTTP errors
    except requests.exceptions.RequestException as e:
        logging.error(f"Error accessing homepage {homepage_url}: {e}")
        return False

    # Parse HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)  # Extract visible text

    # Search for keywords in the text
    for keyword in keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
            logging.info(f"Keyword '{keyword}' found on homepage.")
            return True

    return False


def search_for_cc_indications(repo_instance, homepage):
    """
    Checks if a repository follows the Conventional Commits convention based on specific files and indicators.

    Args:
        :param repo_instance: Repository instance to analyze.
        :param homepage: URL of the repository's homepage.

    Returns:
        bool: True if CC is used, False otherwise.

    """
    local_path = Path(repo_instance.working_tree_dir)
    logging.info("Checking repository for CC indicators")

    cc_detected = False  # Flag for CC indication detection

    # 1. Check package.json for relevant dependencies
    package_json_path = local_path / 'package.json'
    if package_json_path.exists():
        cc_detected = check_package_json(package_json_path) or cc_detected

    # 2. Check for specific configuration files
    cc_detected = check_cc_configuration_files(local_path) or cc_detected

    # 3. Check for Git hooks indicating CC use
    cc_detected = check_git_hooks(local_path) or cc_detected

    # 4. Check documentation and wiki files for CC references
    cc_detected = check_docu_wiki_for_cc(local_path) or cc_detected

    # 5. Check homepage for CC indications if provided
    if homepage:
        logging.info(f"Checking homepage {homepage} for CC indications.")
        homepage_uses_cc = check_homepage_for_cc(homepage)
        cc_detected = homepage_uses_cc or cc_detected
    else:
        logging.info("No homepage provided. Skipping homepage check.")

    if cc_detected:
        logging.info("Found indications of Conventional Commit usage.")
        return True
    else:
        logging.info("No indications of Conventional Commit usage found.")
        return False


def check_package_json(package_json_path):
    """
    Checks package.json for dependencies related to Conventional Commits.

    Args:
        package_json_path (Path): Path to package.json file.

    Returns:
        bool: True if relevant dependencies are found, False otherwise.
    """
    try:
        with open(package_json_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
            dependencies = data.get('dependencies', {})
            dev_dependencies = data.get('devDependencies', {})
            all_dependencies = {**dependencies, **dev_dependencies}
            cc_packages = [
                "commitizen",
                "cz-conventional-changelog",
                "@commitlint/cli",
                "@commitlint/config-conventional",
                "standard-version",
                "semantic-release"
            ]
            found_packages = [dep for dep in cc_packages if dep in all_dependencies]

            if found_packages:
                logging.info(f"Found CC-related dependencies in package.json: {found_packages}")
                return True
    except Exception as e:
        logging.error(f"Error reading package.json: {e}")
    return False


def check_cc_configuration_files(local_path):
    """
    Checks for configuration files indicating the use of Conventional Commits.

    Args:
        local_path (Path): Path to the local repository.

    Returns:
        bool: True if relevant configuration files are found, False otherwise.
    """
    cc_config_files = [
        'commitlint.config.js',
        '.commitlintrc',
        '.commitlintrc.js',
        '.commitlintrc.json',
        '.cz-config.js',
        '.czrc',
        '.versionrc'
    ]

    for config_file in cc_config_files:
        config_path = local_path / config_file
        if config_path.exists():
            logging.info(f"Configuration file found: {config_file}")
            return True
    return False


def check_git_hooks(local_path):
    """
    Checks Git hooks for indications of Conventional Commits usage.

    Args:
        local_path (Path): Path to the local repository.

    Returns:
        bool: True if relevant Git hooks are found, False otherwise.
    """
    git_hooks_path = local_path / '.husky'
    if git_hooks_path.exists() and git_hooks_path.is_dir():
        for hook_file in git_hooks_path.iterdir():
            if hook_file.is_file():
                with open(hook_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'commitlint' in content or 'commitizen' in content:
                        logging.info(f"Git Hook with CC reference found: {hook_file.name}")
                        return True
    else:
        # Alternative check in .git/hooks
        git_hooks_path = local_path / '.git' / 'hooks'
        if git_hooks_path.exists() and git_hooks_path.is_dir():
            for hook_file in git_hooks_path.iterdir():
                if hook_file.is_file() and not hook_file.name.endswith('.sample'):
                    with open(hook_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if 'commitlint' in content or 'commitizen' in content:
                            logging.info(f"Git Hook with CC reference found: {hook_file.name}")
                            return True
    return False


def check_docu_wiki_for_cc(local_path):
    """
    Searches documentation and wiki files for mentions of Conventional Commits.

    Args:
        local_path (Path): Path to the local repository.

    Returns:
        bool: True if relevant references are found, False otherwise.
    """
    doc_files = [
        'README.md',
        'CONTRIBUTING.md',
        'DEVELOPING.md'
    ]

    keywords = [
        "Conventional Commits",
        "Conventional Commit",
        "Conventional Changelog",
        "Commit Message Convention",
        "Commit Guidelines",
        "commitizen",
        "commitlint",
        "standard-version",
        "semantic-release"
    ]

    # Check main documentation files
    for doc_file in doc_files:
        doc_path = local_path / doc_file
        if doc_path.exists():
            with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for keyword in keywords:
                    if re.search(r'\b' + re.escape(keyword) + r'\b', content, re.IGNORECASE):
                        logging.info(f"Keyword '{keyword}' found in {doc_file}")
                        return True

    # Check wiki for relevant references
    wiki_dir = local_path / '.wiki'
    if wiki_dir.exists():
        for root, dirs, files in os.walk(wiki_dir):
            for file in files:
                if file.endswith(('.md', '.txt', '.rst', '.adoc')):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            for keyword in keywords:
                                if re.search(r'\b' + re.escape(keyword) + r'\b', content, re.IGNORECASE):
                                    logging.info(f"Keyword '{keyword}' found in Wiki file: {file_path}")
                                    return True
                    except Exception as e:
                        logging.warning(f"Error reading file {file_path}: {e}")
    else:
        logging.debug("No wiki directory found. Skipping wiki check.")

    return False
