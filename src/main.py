import logging
import colorlog

from RQ1 import analyze_rq1
from RQ2 import analyze_rq2
from constants import COMMIT_ANALYSIS_RESULTS
from data_saver import load_all_repositories_data, load_dataset
from process_repository import process_repository


def main():
    """
    Main function to execute the analysis workflow.
    """
    # Set up directories and logging
    setup_environment()

    # Load and process the dataset
    dataset = load_dataset()
    # process_repositories(dataset)

    # Load enriched data
    repos, summaries, commits = load_enriched_data()

    # Research Question 1 Analysis
    analyze_rq1(repos, summaries, commits, dataset)

    # Research Question 2 Analysis
    analyze_rq2(repos)


def set_logging():
    # Erstellen Sie einen Logger
    logger = logging.getLogger()

    # Legen Sie den Log-Level fest
    logger.setLevel(logging.INFO)

    # Definieren Sie das Log-Format mit Farben
    log_format = (
        '%(log_color)s [%(levelname)s] %(message)s'
    )

    # Definieren Sie die Farben für die Log-Levels
    log_colors = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
        'COUNTER': 'blue'
    }

    # Erstellen Sie einen Handler für die Konsole
    handler = logging.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(log_format, log_colors=log_colors))

    # Fügen Sie den Handler dem Logger hinzu
    logger.handlers = [handler]

    return logger


def setup_environment():
    """
    Sets up the necessary directories and logging configuration.
    """
    COMMIT_ANALYSIS_RESULTS.mkdir(exist_ok=True)
    set_logging()


def process_repositories(dataset):
    """
    Processes each repository in the dataset.
    """
    for repo_data in dataset:
        process_repository(repo_data)


def load_enriched_data():
    """
    Loads all enriched repository data and returns summaries and commits.
    """
    repos = load_all_repositories_data(COMMIT_ANALYSIS_RESULTS)
    summaries = []
    commits = []
    for repo in repos:
        summary = repo.get('analysis_summary')
        repo_commits = repo.get('commits')
        if summary:
            summaries.append(summary)
        if repo_commits:
            commits.extend(repo_commits)
    return repos, summaries, commits


if __name__ == "__main__":
    main()
