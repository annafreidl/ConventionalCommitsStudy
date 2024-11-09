# Standard library imports
import logging
import os
import shutil
import stat
from pathlib import Path

# Third-party library imports
import requests
from git import Repo, GitCommandError
from git.remote import RemoteProgress
from tqdm import tqdm

# Local imports
from constants import ERROR, GITHUB_TOKEN, TEMP


class CloneProgress(RemoteProgress):
    """
    Tracks and displays the progress of the repository cloning process.
    """

    def __init__(self):
        super().__init__()
        self.pbar = tqdm()  # Initialize a progress bar

    def update(self, op_code, cur_count, max_count=None, message=""):
        # Update the progress bar with current and maximum counts
        self.pbar.total = max_count
        self.pbar.n = cur_count
        self.pbar.refresh()  # Refresh to display the current progress


def handle_remove_readonly(func, path):
    """
    Remove the 'read-only' attribute from files or directories to allow deletion.

    Args:
        func: The function to apply (e.g., os.remove).
        path: The path of the file or directory.
    """
    os.chmod(path, stat.S_IWRITE)  # Set write permissions
    func(path)  # Attempt to remove the file or directory


# Function to log errors during the cloning or processing of repositories
def log_error(repo_name, repo_url, error_message, language):
    """
    Logs errors to a predefined error file.

    Args:
        repo_name (str): Name of the repository.
        repo_url (str): URL of the repository.
        error_message (str): Error message to be logged.
        language (str): Programming language of the repository.
    """
    with ERROR.open("a") as f:
        f.write(f"Repository: {repo_name}, URL: {repo_url}, Error: {error_message}, Language: {language}\n")


def clone_wiki_repository(repo, repo_dir, repo_name):
    """
    Attempts to clone the wiki for a repository if it exists.

    Args:
        repo (dict): Dictionary containing repository metadata.
        repo_dir (Path): Directory where the main repository is cloned.
        repo_name (str): Name of the repository.
    """
    # Check if the repository has a wiki associated with it
    if repo.get("has_wiki", False):
        wiki_url = repo["clone_url"].replace(".git", ".wiki.git")  # Generate the wiki URL
        wiki_dir = repo_dir / ".wiki"  # Define directory for the cloned wiki

        if wiki_dir.exists():
            logging.info(f"Wiki repository for {repo['name']} already exists.")
        else:
            logging.info(f"Attempting to clone wiki for {repo['name']} from {wiki_url}")
            try:
                headers = {
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Python Script"  # GitHub requires a User-Agent header
                }
                response = requests.get(wiki_url, headers=headers)

                if response.status_code == 200:
                    Repo.clone_from(wiki_url, wiki_dir)
                    logging.info("Wiki cloned successfully.")
                elif response.status_code == 404:
                    logging.warning("Wiki does not exist.")
                else:
                    logging.warning(
                        f"Unexpected status code when accessing the wiki: {response.status_code}")
            except GitCommandError as e:
                logging.warning(f"Error cloning the wiki repository for {repo_name}: {e}")
                if "Repository not found" in str(e) or "Repository disabled" in str(e):
                    logging.warning(
                        f"The wiki repository for {repo_name} is either disabled or not available.")
                else:
                    logging.warning(f"An unspecified Git error occurred: {e}")
                # Continue processing even if wiki cloning fails


def clone_repository(repo):
    """
    Clones a repository or loads it if it already exists.

    Args:
        repo (dict): A dictionary containing repository metadata, including "name", "clone_url", and "language".

    Returns:
        Repo instance if successful; None if cloning/loading fails.
    """
    repo_name = repo["name"]
    repo_url = repo["clone_url"]
    # If language is specified, use it in the directory name; otherwise, use "Language_Unknown" as fallback
    repo_language = f"Language-{repo['language']}" if repo["language"] else "Language_Unknown"

    # Create a subfolder for each language, organizing repos by language
    language_dir = Path(TEMP) / repo_language
    language_dir.mkdir(parents=True, exist_ok=True)

    # Define the final directory for the cloned repository and a temporary directory for cloning
    repo_dir = language_dir / repo_name
    repo_dir_temp = language_dir / f"{repo_name}_temp"

    if repo_dir.exists():
        # If the repository already exists, attempt to load it
        logging.info(f"Repository {repo_name} already exists.")
        try:
            repo_instance = Repo(repo_dir)
            # Optional: Uncomment below to update the repository
            # repo_instance.remotes.origin.pull()
        except GitCommandError as e:
            # If loading fails, log a warning
            logging.warning(f"Error loading repository {repo_name}: {e}")
            repo_instance = None
    else:
        # If the temporary directory exists, a previous cloning attempt was interrupted
        if repo_dir_temp.exists():
            logging.warning(f"Incomplete repository found. Deleting temporary directory {repo_dir_temp}")
            shutil.rmtree(repo_dir_temp, onerror=handle_remove_readonly)

        logging.info(f"Cloning {repo_name} from {repo_url} into {language_dir}")
        try:
            # Set environment variables to ensure UTF-8 encoding is handled properly
            env = os.environ.copy()
            env['LANG'] = 'en_US.UTF-8'
            env['PYTHONIOENCODING'] = 'utf-8'

            # Clone the repository into the temporary directory
            Repo.clone_from(repo_url, repo_dir_temp, progress=CloneProgress(), env=env)
            # Rename the temporary directory to the final directory
            os.rename(repo_dir_temp, repo_dir)
            # Reload the cloned repository as a Repo instance
            repo_instance = Repo(repo_dir)
        except GitCommandError as e:
            # Catch Git errors, such as repository unavailability or cloning failures
            logging.warning(f"Error cloning repository {repo_name}: {e}")
            log_error(repo_name, repo_url, repo_language, str(e))
            if "Repository not found" in str(e) or "Repository disabled" in str(e):
                logging.warning(f"The repository {repo_name} is either disabled or no longer available.")
            else:
                logging.warning(f"An unspecified Git error occurred: {e}")
            return None  # Return None if cloning fails

    # Attempt to clone the repository's wiki if it exists
    clone_wiki_repository(repo, repo_dir, repo_name)

    return repo_instance  # Return the Repo instance, whether cloned or loaded
