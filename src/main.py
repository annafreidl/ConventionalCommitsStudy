import json
import logging
import os
import statistics
from collections import defaultdict
import datetime
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dateutil import parser

import ijson as ijson
import numpy as np
import pandas as pd
import requests
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

from RQ2 import load_and_filter_commits
from analyzer import aggregate_commit_types
from constants import PLOTS

matplotlib.use("pgf")
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    'font.family': 'serif',
    'text.usetex': True,
    'pgf.rcfonts': False,
})

from RQ1 import set_logging, calculate_adoption_rate_by_age, calculate_adoption_rate_by_size, \
    calculate_adoption_rate_by_project_type
from data_enricher import enrich_commits
from data_saver import load_analysis_summaries, save_to_json
from process_repository import process_repository, convert_date_format
from repository_manager import GITHUB_TOKEN
from visualization_utils import plot_complete_classification

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
RESULTS = ROOT / "results" / "commit_messages_alt"
YAML = ROOT / "data" / "test.yaml"
CLASSIFICATION_FILE = ROOT / "results" / "repository_classifications.json"


def median_stars(repositories):
    stars_list = []

    for repo_data in repositories:
        stars = repo_data.get('stargazers_count')
        stars_list.append(stars)

    if stars_list:
        median_stars = statistics.median(stars_list)
        print(f"Median der Sterne: {round(median_stars)}")


def average_contributors():
    contributor_count_list = []
    for filename in os.listdir(RESULTS):
        filepath = os.path.join(RESULTS, filename)
        with open(filepath, 'r') as f:
            logging.info(f"Loading summary from {filepath}")
            data = json.load(f)
            commits = data.get('commits', [])

            contributors = set()
            for commit in commits:
                author = commit.get('author', {})  # Adjust this based on your JSON structure
                if author:
                    contributors.add(author)
            contributor_count_list.append(len(contributors))

    if contributor_count_list:
        print(contributor_count_list)
        avg_contributors = statistics.mean(contributor_count_list)
        print(f'Minimale Anzahl der Mitwirkenden in allen Projekten: {avg_contributors}')
    else:
        print('Keine Projekte gefunden.')


def total_commits():
    total_commits = 0

    for filename in os.listdir(RESULTS):
        filepath = os.path.join(RESULTS, filename)
        with open(filepath, 'r') as f:
            logging.info(f"Loading summary from {filepath}")
            data = json.load(f)
            summary = data.get('analysis_summary', [])
            total_commits += summary.get('total_commits', 0)

    print(f"Gesamtzahl an Commits: {total_commits}")


def calc_total_commits(repos, headers):
    total_sum_commits = 0

    for repo in repos:
        repo_url = repo['clone_url'].replace('.git',
                                             '')  # Angenommen, repos sind von der API, z.B. `repo['html_url']` oder `repo['clone_url']`
        repo_name = repo_url.split('/')[-2] + '/' + repo_url.split('/')[-1]  # Benutzer/Repo-Name formatieren

        # Erste Seite der Commits abrufen
        api_url = f'https://api.github.com/repos/{repo_name}/commits?per_page=100'
        response = requests.get(api_url, headers=headers)

        if response.status_code != 200:
            print(f'Error fetching commits for {repo["name"]}: {response.status_code}')
            continue

        number_of_commits_in_first_page = len(response.json())
        repo_sum = 0

        if number_of_commits_in_first_page >= 100:
            links = response.links

            if 'last' in links:
                last_page_url = links['last']['url']
                page_num = int(last_page_url.split('page=')[-1])

                repo_sum += (page_num - 1) * 100  # Die Anzahl der Seiten minus eins multipliziert mit Page Size
                repo_sum += len(
                    requests.get(last_page_url, headers=headers).json())  # Anzahl der Commits auf der letzten Seite

        else:
            repo_sum += number_of_commits_in_first_page

        print(f'Commits for {repo["name"]}: {repo_sum}')
        total_sum_commits += repo_sum

    print(f'TOTAL COMMITS: {total_sum_commits}')


def calculate_adoption_trends(summaries, file_path):
    print("Summaries loaded")

    adopted_by_year = defaultdict(int)
    not_adopted_by_year = defaultdict(int)
    existing_repos_by_year = defaultdict(int)

    current_year = datetime.now(timezone.utc).year

    for summary in summaries:
        # Convert creation date to year (Integer)
        created_at = int(datetime.strptime(summary['created_at'], "%Y-%m-%d").year)
        cc_adoption_date = summary.get('cc_adoption_date')

        if cc_adoption_date:
            # Convert adoption date to year (Integer)
            adoption_year = int(datetime.strptime(cc_adoption_date, "%Y-%m-%d").year)
            # Count the repository as "adopted" from the adoption year onwards
            for year in range(created_at, adoption_year + 1):
                existing_repos_by_year[year] += 1
            for year in range(adoption_year, current_year + 1):
                adopted_by_year[year] += 1
                existing_repos_by_year[year] += 1
        else:
            # Count the repository as "not adopted" from the creation year onwards
            for year in range(created_at, current_year + 1):
                not_adopted_by_year[year] += 1
                existing_repos_by_year[year] += 1

    # Ensure all years are covered
    start_year = 2017
    end_year = max(existing_repos_by_year.keys()) if existing_repos_by_year else current_year
    years = list(range(start_year, end_year + 1))

    # Calculate adoption ratio (percentage)
    adoption_ratio = [
        100 * adopted_by_year[year] / existing_repos_by_year[year] if existing_repos_by_year[year] > 0 else 0
        for year in years
    ]

    # Calculate the number of adopted projects each year (cumulative)
    cumulative_adopted = []
    total_adopted = 0
    for year in years:
        total_adopted += adopted_by_year[year]
        cumulative_adopted.append(total_adopted)

    # Calculate scaled adoption ratio (1000 * ratio) - Optional: Consider removing or modifying
    scaled_adoption_ratio = [1000 * ratio for ratio in adoption_ratio]

    # Adjust font settings for LaTeX compatibility
    plt.rc('font', size=10)  # Standard font size
    plt.rc('axes', titlesize=12)  # Title font size
    plt.rc('axes', labelsize=10)  # Axis labels font size
    plt.rc('xtick', labelsize=8)  # X-axis tick labels font size
    plt.rc('ytick', labelsize=8)  # Y-axis tick labels font size
    plt.rc('legend', fontsize=8)  # Legend font size
    plt.rc('font', family='serif')  # Use a serif font for LaTeX compatibility
    # Plot 2: Adoption Ratio (Percentage) Over Time
    plt.figure(figsize=(3.101, 2.326))
    plt.plot(years, adoption_ratio, 'o-', color='darkgreen', label='Adoption Ratio (%)')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(PLOTS / file_path)
    plt.show()

def calculate_adoption_trends_overall(summaries, file_path):
    """
    Plots the adoption trends of Conventional Commits (CC) over time, showing both
    the number of CC-adopted repositories and the total number of existing repositories.

    Parameters:
        summaries (list of dict): The dataset containing repository summaries.
        file_path (str or Path): The filename/path to save the plot.
    """
    print("Summaries loaded")

    # Initialize defaultdicts for tracking counts per year
    adopted_by_year = defaultdict(int)
    existing_repos_by_year = defaultdict(int)

    # Get the current year in UTC
    current_year = datetime.now(timezone.utc).year

    for summary in summaries:
        # Extract creation year
        created_at_str = summary.get('created_at')
        if not created_at_str:
            continue  # Skip if creation date is missing
        try:
            created_at = datetime.strptime(created_at_str, "%Y-%m-%d").year
        except ValueError:
            print(f"Invalid creation date format: {created_at_str}")
            continue  # Skip if date format is invalid

        # Extract adoption year if available
        cc_adoption_date_str = summary.get('cc_adoption_date')
        if cc_adoption_date_str:
            try:
                adoption_year = datetime.strptime(cc_adoption_date_str, "%Y-%m-%d").year
            except ValueError:
                print(f"Invalid adoption date format: {cc_adoption_date_str}")
                adoption_year = None
        else:
            adoption_year = None

        # Increment existing repositories from creation to current year
        for year in range(created_at, current_year + 1):
            existing_repos_by_year[year] += 1

        # If adopted, increment adopted repositories from adoption year to current year
        if adoption_year and adoption_year >= created_at:
            for year in range(adoption_year, current_year + 1):
                adopted_by_year[year] += 1

    # Define the range of years to plot
    start_year = 2017
    end_year = current_year
    years = list(range(start_year, end_year + 1))

    # Calculate adoption ratios and existing ratios
    adoption_ratio = [adopted_by_year[year] for year in years]
    existing_ratio = [existing_repos_by_year[year] for year in years]

    # Optional: Calculate cumulative adoption for alternative plotting
    cumulative_adopted = np.cumsum(adoption_ratio)

    # Create DataFrame for plotting
    plot_df = pd.DataFrame({
        'Year': years,
        'CC Adopted Repositories': adoption_ratio,
        'Existing Repositories': existing_ratio
    })

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(plot_df['Year'], plot_df['CC Adopted Repositories'], marker='o', linestyle='-', color='darkgreen', label='CC Adopted Repositories')
    plt.plot(plot_df['Year'], plot_df['Existing Repositories'], marker='s', linestyle='--', color='darkblue', label='Existing Repositories')
    plt.xlabel('Year')
    plt.ylabel('Number of Repositories')
    plt.title('Number of CC-Adopted and Existing Repositories Over Time')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.tight_layout()

    # Save the plot
    plt.savefig(ROOT / "results" / "diagrams" / file_path, dpi=300)
    plt.show()

colors = ['#e6f4e6', '#c3e6c3', '#a1d8a1', '#7eca7e', '#5cbd5c', '#4da64d', '#3d8c3d']


def plot_adoption_rate_by_language(summaries, file_path):
    language_stats = defaultdict(lambda: {'total_repos': 0, 'adopted_repos': 0})

    for summary in summaries:
        language = summary.get('language', 'Unknown')
        language_stats[language]['total_repos'] += 1
        if summary.get('cc_adoption_date'):
            language_stats[language]['adopted_repos'] += 1

    languages = list(language_stats.keys())
    adoption_rates = [
        (language_stats[lang]['adopted_repos'] / language_stats[lang]['total_repos']) * 100
        if language_stats[lang]['total_repos'] > 0 else 0
        for lang in languages
    ]

    # Create DataFrame for plotting
    df = pd.DataFrame({
        'Language': languages,
        'Adoption Rate (%)': adoption_rates
    }).sort_values(by='Adoption Rate (%)', ascending=False)

    # Assuming 'df' is your DataFrame containing the plot data
    df['Language'] = df['Language'].apply(escape_latex)

    plt.figure(figsize=(6.202, 4.652))
    ax =sns.barplot(data=df, x='Adoption Rate (%)', y='Language', color=colors[4])
    ax.set_xlabel('')
    ax.set_ylabel('')
    plt.tight_layout()
    plt.savefig(PLOTS / file_path)
    plt.show()


def plot_adoption_rate_by_size(summaries, file_path):
    # Extrahiere die Projektgröße und Adoptionsrate
    sizes = []
    adoption_rates = []
    for summary in summaries:
        size = summary.get('size', 0)
        adoption_rate = summary.get('overall_cc_adoption_rate', 0)
        sizes.append(size)
        adoption_rates.append(adoption_rate)

    # In Kategorien einteilen: Klein, Mittel, Groß
    size_bins = [0, 1e4, 1e5, 1e6, 1e7, np.inf]
    size_labels = ['Sehr klein', 'Klein', 'Mittel', 'Groß', 'Sehr groß']
    size_categories = pd.cut(sizes, bins=size_bins, labels=size_labels)

    # Berechne durchschnittliche Adoptionsrate pro Kategorie
    df = pd.DataFrame({'Size Category': size_categories, 'Adoption Rate (%)': adoption_rates})
    category_avg_adoption = df.groupby('Size Category').mean().reset_index()

    # Entferne Kategorien ohne Daten
    category_avg_adoption = category_avg_adoption.dropna()

    # Plot
    plt.figure(figsize=(10, 6))
    sns.barplot(data=category_avg_adoption, x='Size Category', y='Adoption Rate (%)', palette='Blues')
    plt.xlabel('Projektgrößenkategorie')
    plt.ylabel('Durchschnittliche Adoptionsrate (%)')
    plt.title('Durchschnittliche Adoptionsrate von Conventional Commits nach Projektgröße')
    plt.tight_layout()
    plt.savefig(PLOTS / file_path)
    plt.show()


def plot_commit_types_impact_on_codebase_metrics_bar(commits, file_path, figsize=(6.202, 4.652)):
    """
    Plots a grouped bar chart showing Insertions and Deletions for each Commit Type.

    Parameters:
        commits (list of dict): The dataset containing commit details.
        output_filename (str or Path): The filename/path to save the PGF or PDF plot.
        figsize (tuple): The size of the figure in inches.
    """
    # Filter conventional commits and extract relevant data
    data = []
    for commit in commits:
        if not commit.get('is_conventional'):
            continue
        ctype = commit.get('cc_type', 'Unspecified')
        insertions = commit.get('insertions', 0)
        deletions = commit.get('deletions', 0)
        data.append({'Commit Type': ctype, 'Insertions': insertions, 'Deletions': deletions})

    # Create DataFrame
    df = pd.DataFrame(data)

    if df.empty:
        print("No conventional commits found in the dataset.")
        return

    # Aggregate Data: Sum of Insertions and Deletions per Commit Type
    agg_df = df.groupby('Commit Type').agg({'Insertions': 'sum', 'Deletions': 'sum'}).reset_index()

    # Transform to long format for Seaborn
    plot_df = agg_df.melt(id_vars='Commit Type', value_vars=['Insertions', 'Deletions'],
                          var_name='Metric', value_name='Count')

    # Escape LaTeX special characters in Commit Types
    plot_df['Commit Type'] = plot_df['Commit Type'].apply(lambda x: escape_latex(x) if x else 'Unspecified')

    # Adjust font settings for LaTeX compatibility
    plt.rc('font', size=10)  # Standard font size
    plt.rc('axes', titlesize=12)  # Title font size
    plt.rc('axes', labelsize=10)  # Axis labels font size
    plt.rc('xtick', labelsize=8)  # X-axis tick labels font size
    plt.rc('ytick', labelsize=8)  # Y-axis tick labels font size
    plt.rc('legend', fontsize=8)  # Legend font size
    plt.rc('font', family='serif')  # Use a serif font for LaTeX compatibility

    # Create the bar chart
    plt.figure(figsize=figsize)
    ax = sns.barplot(data=plot_df, x='Commit Type', y='Count', hue='Metric', palette='Set2')
    plt.legend(title='Metric', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_xlabel('')
    ax.set_ylabel('')
    plt.tight_layout()

    # Save the plot
    plt.savefig(PLOTS / file_path)
    plt.show()


def escape_latex(text):
    if not isinstance(text, str):
        return text
    # Handle specific cases first
    text = text.replace('C#', 'C\\#')
    # Escape other special characters
    special_chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}'
    }
    for char, esc in special_chars.items():
        text = text.replace(char, esc)
    return text


def plot_comparative_conventional_custom_commits(summaries_adopted, file_path, figsize=(6.202, 4.652)):
    """
    Plots a 100% stacked bar chart showing the percentage distribution of Conventional Commits,
    Custom Commits, and Non-CC Commits for the top 20 repositories based on Conventional Commits.

    Parameters:
        summaries_adopted (list of dict): The dataset containing repository summaries.
        output_filename (str or Path): The filename/path to save the PGF plot.
        figsize (tuple): The size of the figure in inches.
    """
    data = []
    for summary in summaries_adopted:
        conventional = sum(summary.get('cc_type_distribution', {}).values())
        custom = sum(summary.get('custom_type_distribution', {}).values())
        non_cc = summary.get('total_commits', 0) - conventional - custom
        data.append({'Repository': summary['name'], 'Conventional Commits': conventional, 'Custom Commits': custom,
                     'Non-CC Commits': non_cc})

    df = pd.DataFrame(data)

    # Aggregate by repository
    df_agg = df.groupby('Repository').sum()

    # Select top 20 repositories based on Conventional Commits
    df_top = df_agg.sort_values(by='Conventional Commits', ascending=False).head(20)

    # Calculate percentages
    df_percentage = df_top.div(df_top.sum(axis=1), axis=0) * 100

    # Define colors for each commit type
    colors = {
        'Conventional Commits': 'skyblue',
        'Custom Commits': 'salmon',
        'Non-CC Commits': 'lightgreen'
    }

    # Create the stacked bar chart
    plt.figure(figsize=figsize)
    bottom = None
    for metric in ['Conventional Commits', 'Custom Commits', 'Non-CC Commits']:
        plt.bar(
            df_percentage.index,
            df_percentage[metric],
            bottom=bottom,
            label=metric,
            color=colors.get(metric, 'grey')
        )
        if bottom is None:
            bottom = df_percentage[metric]
        else:
            bottom += df_percentage[metric]

    plt.xlabel('Repository')
    plt.ylabel('Percentage of Commits (%)')
    plt.title('Distribution of Commit Types in Top 20 Repositories')
    plt.legend(title='Commit Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Save the plot
    plt.savefig(ROOT / "results" / "diagrams" / file_path)
    plt.show()


def plot_commit_type_heatmap(summaries_adopted):
    # Aggregate commit types per repository
    commit_types = ['feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'build', 'ci', 'chore', 'revert']
    data = []
    for summary in summaries_adopted:
        row = [summary['cc_type_distribution'].get(ctype, 0) for ctype in commit_types]
        data.append(row)

    df = pd.DataFrame(data, columns=commit_types)

    # Compute correlation matrix or simply average counts
    heatmap_data = df.mean().sort_values(ascending=False).values.reshape(-1, 1)
    labels = df.columns.sort_values(ascending=False)

    plt.figure(figsize=(8, 12))
    sns.heatmap(heatmap_data, annot=True, fmt=".2f", yticklabels=labels, cmap='YlGnBu',
                cbar_kws={'label': 'Average Commit Count'})
    plt.xlabel('')
    plt.title('Heatmap of Average Commit Type Usage Across Repositories')
    plt.tight_layout()
    plt.savefig(ROOT / "results" / "diagrams" / 'commit_type_heatmap.pdf')
    plt.show()


def plot_correlation_matrix(summaries):
    df = pd.DataFrame([{
        'Total Commits': summary.get('total_commits', 0),
        'Conventional Commits': summary.get('conventional_commits', 0),
        'Unconventional Commits': summary.get('unconventional_commits', 0),
        'CC Type Commits': summary.get('cc_type_commits', 0),
        'Custom Type Commits': summary.get('custom_type_commits', 0),
        'Project Size': summary.get('size', 0),
        'Adoption Rate (%)': summary.get('overall_cc_adoption_rate', 0)
    } for summary in summaries])

    correlation = df.corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5)
    plt.title('Correlation Matrix of Commit Metrics')
    plt.tight_layout()
    plt.savefig(ROOT / "results" / "diagrams" / 'correlation_matrix.pdf')
    plt.show()


if __name__ == "__main__":
    logger = set_logging()
    RESULTS.mkdir(exist_ok=True)
    repos = load_dataset(YAML)

    file_path = ROOT / "results" / "summaries.json"
    commits_file_path = ROOT / "results" / "commits.json"

    with open(file_path, 'r') as json_file:
        summaries = json.load(json_file)
        json_file.close()

    with open(commits_file_path, 'r', encoding='utf-8') as json_file:  # Encoding hier auf 'utf-8' setzen
        commits = []
        for item in ijson.items(json_file, 'item'):
            commits.append(item)
        json_file.close()

    print("Summaries loaded")

    summaries_adopted = [s for s in summaries if s.get('cc_adoption_date') is not None]
    summaries_typescript = [s for s in summaries if s.get('language') == 'TypeScript']


    current_date = datetime.now(timezone.utc)

    languages = ['JavaScript', 'Python', 'Java', 'C++', 'C#', 'PHP', 'Rust', 'Go', 'C', 'TypeScript']

    for language in languages:
        alter_list = []
        for summary in summaries:
            if summary.get('language') == language:
                created_at_str = summary.get('created_at')
                created_at = parser.parse(created_at_str)
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                else:
                    created_at = created_at.astimezone(timezone.utc)
                age = (current_date - created_at).days / 365.25
                alter_list.append(age)

        durchschnitt = sum(alter_list) / len(alter_list)
        print(f"Durchschnittliche Alter von {language}:", durchschnitt)


    # RQ1
    # Adoption Rate by Programming Language
    # for file in os.listdir(ROOT / "results" / "commit_messages_alt"):
    #     if file.endswith(".json"):
    #         with open(ROOT / "results" / "commit_messages_alt" / file, 'r') as f:
    #             data = json.load(f)
    #             summary = data.get('analysis_summary', [])
    #             name = summary.get('name')
    #             commits = data.get('commits', [])
    #         if summary.get('cc_indication'):
    #             if summary.get('cc_adoption_date') is None:
    #                 print(summary.get('name'))
    #                 commits_reversed = commits[::-1]
    #                 # binäre Sequenz erstellen aus Commits (1 = CC, 0 = Nicht-CC)
    #                 commit_sequence = [1 if commit.get("is_conventional") else 0 for commit in commits_reversed]
    #                 plot_heatmap_not_cc(commit_sequence, name)


    # Projektübergreifend
    plot_commit_type_heatmap(summaries_adopted)
    plot_correlation_matrix(summaries)
    aggregate_commit_types(summaries_adopted, 'cc_type_distribution')
    aggregate_commit_types(summaries_adopted, 'custom_type_distribution')

    # Sehr gut!
    plot_adoption_rate_by_language(summaries, 'adoption_rate_by_language.pdf')

    # interessant!
    calculate_adoption_rate_by_project_type(summaries, "adoption_rate_by_project_type.pdf")

    # Trend in % von CC-Adopted Repos
    calculate_adoption_trends(summaries, "adoption_ratio_over_time.pdf")

    # Commitverteilung

    # sehr gut!
    plot_commit_types_impact_on_codebase_metrics_bar(commits, 'commit_types_impact_on_codebase_metrics_bar.pdf')

    calculate_adoption_trends_overall(summaries, 'adoption_ratio_overall.pdf')

    calculate_adoption_rate_by_age(summaries, 'adoption_rate_by_project_age.pdf')

    calculate_adoption_rate_by_size(summaries, 'adoption_rate_by_project_size.png')

    plot_adoption_rate_by_size(summaries, "adoption_rate_by_project_size_binned.png")







    # classification_file = ROOT / "results" / "repository_classifications.json"
    # plot_complete_classification(classification_file, ROOT / "results")

    # Beispielaufruf:
    # with open('repos.json') as f:
    #     repos = json.load(f)
    # token = 'DEIN_GITHUB_TOKEN'
    # commit_counts = fetch_commit_count(repos, token)
    # print(commit_counts)

    i = 0
    stars_list = []

    # for repo_data in repos:
    #     i += 1
    #     process_repository(repo_data, RESULTS)
    #     logging.info(f"Processed {i} repos")
    # classification = load_classification()

    # for file_name in os.listdir(RESULTS):
    #     if file_name.endswith('.json'):
    #         json_file_path = os.path.join(RESULTS, file_name)
    #         with open(json_file_path, 'r') as f:
    #             data = json.load(f)
    #             summary = data.get('analysis_summary', [])
    #             enriched_commits = data.get('commits', [])
    #             name = summary.get('name')
    #             language = summary.get('language')
    #
    #             found = False
    #
    #             classification_name = classification[language][name]
    #             if classification_name in ["nutzen CC und als Vorgabe erkennbar",
    #                                           "Erwaehnung von CC, aber wird nicht genutzt"]:
    #                 found = True
    #
    #             summary['cc_indication'] = found
    #             print(f"{name}: {found} ")
    #             save_to_json(enriched_commits, summary, json_file_path)
    #
    #
    #             # summary['created_at'] = convert_date_format(summary['created_at'])
    #             # repo_name = file_name.split('.')[0]
    #             # summary['name'] = repo_name.split("_")[0]
    #             # summary.pop('updated_at')
    #             # summary.pop('forks_count')
    #             # summary.pop('pushed_at')
    #             # commits = data.get('commits', [])
    #             # commits_enriched, summary_enriched = enrich_commits(commits, summary)
    #             # output_path = ROOT / "results" / "commit_messages_alt"
    #             # json_new_file_path = os.path.join(output_path, file_name)
    #             # save_to_json(commits_enriched, summary_enriched, json_new_file_path)
    #

    # median_stars(repos)
    # average_contributors()

    # total_commits()

    # Laden der Zusammenfassungen
    # summaries = load_analysis_summaries(RESULTS)
    #
    # # Berechnung der Adoptionsrate
    # calculate_adoption_rate(summaries)
    #
    # summaries_adopted = [s for s in summaries if s.get('cc_adoption_date') is not None]
    #
    # size_vs_cc_usage(summaries)
    #
    # # Analyse der Commit-Typ-Verteilung pro Projekt
    # aggregate_commit_types(summaries_adopted, 'cc_type_distribution')
    # aggregate_commit_types(summaries_adopted, 'custom_type_distribution')
    #
    # # Berechnung der Adoptionsrate pro Sprache
    # calculate_adoption_rate_by_language(summaries)

    # plot_cc_adoption_dates(RESULTS)
