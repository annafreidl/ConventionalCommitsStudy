from pathlib import Path

from analyzer import calculate_adoption_rate, aggregate_commit_types, calculate_adoption_rate_by_language, \
    size_vs_cc_usage
from data_saver import load_dataset, load_analysis_summaries
from process_repository import process_repository

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
RESULTS = ROOT / "results" / "commit_messages"
YAML = ROOT / "data" / "dataset.yaml"

if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    repos = load_dataset(YAML)

    # # organize_existing_repos(repos)
    #
    # i = 0
    #
    # for repo_data in repos:
    #     i += 1
    #     process_repository(repo_data, RESULTS)
    #     print(f"Processed {i} repos")

    # Laden der Zusammenfassungen
    summaries = load_analysis_summaries(RESULTS)

    # Berechnung der Adoptionsrate
    calculate_adoption_rate(summaries)

    summaries_adopted = [s for s in summaries if s.get('cc_adoption_date') is not None]

    size_vs_cc_usage(summaries)

    # Analyse der Commit-Typ-Verteilung pro Projekt
    aggregate_commit_types(summaries_adopted, 'cc_type_distribution')
    aggregate_commit_types(summaries_adopted, 'custom_type_distribution')

    # Berechnung der Adoptionsrate pro Sprache
    calculate_adoption_rate_by_language(summaries)

    # plot_cc_adoption_dates(RESULTS)
