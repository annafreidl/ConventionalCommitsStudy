import logging
import os

import colorlog as colorlog
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from datetime import datetime, timezone, timedelta
from dateutil import parser
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime

from collections import Counter

from analyzer import aggregate_commit_types
from constants import PLOTS
from data_saver import load_analysis_summaries, load_from_json
from dataset import load_dataset
from process_repository import process_repository

COUNTER_LEVEL = 25
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
RESULTS = ROOT / r"results" / r"commit_messages"
YAML = ROOT / "data" / "dataset.yaml"

plt.rcParams.update({
    "pgf.texsystem": "pdflatex",  # LaTeX engine
    'font.family': 'serif',  # Use serif fonts
    'text.usetex': True,  # Use LaTeX for all text
    'pgf.rcfonts': False,  # Disable Matplotlib RC fonts
})


# RQ1: Analysing the consistency of CC applications and the distribution and frequency
# of commit types.
#
# – Adoption Rate: To what extent are CC guidelines being followed in different open
# source projects? Are there differences in adoption rates based on factors such as
# programming language, project size, or community activity?

# – Consistency: How consistently are CC guidelines applied within projects that have
# adopted them? Are there discrepancies in usage patterns among individual devel-
# opers within the same project?

# – Commit Type Distribution: What is the frequency distribution of different commit
# types (e.g., bug fixes, feature additions, documentation updates) within projects?
# Are there patterns related to project type, development phase, or team size?

# – Impact on Project Management: How does the distribution of commit types influ-
# ence project management tasks such as effort estimation and resource allocation?
# Is it possible to identify correlations between commit patterns and project outcomes

def counter(self, message, *args, **kws):
    if self.isEnabledFor(COUNTER_LEVEL):
        self._log(COUNTER_LEVEL, message, args, **kws)


def set_logging():
    logging.addLevelName(COUNTER_LEVEL, 'COUNTER')
    logging.Logger.counter = counter

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


def calculate_adoption_rate(summaries):
    total_repos = len(summaries)
    adopted_repos = sum(1 for s in summaries if s.get('cc_adoption_date', 0) is not None)
    adoption_rate = adopted_repos / total_repos if total_repos > 0 else 0
    print(f"Gesamtzahl der Repositories: {total_repos}")
    print(f"Repositories mit CC-Nutzung: {adopted_repos}")
    print(f"Adoptionsrate: {adoption_rate:.2%}")

    plot_adoption_rate(adopted_repos, total_repos)


def plot_adoption_rate(adopted_repos, total_repos):
    not_adopted = total_repos - adopted_repos

    labels = ['CC-Adoptiert', 'Nicht CC-Adoptiert']
    sizes = [adopted_repos, not_adopted]
    colors = ['green', 'red']

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title('Adoptionsrate von Conventional Commits')
    plt.axis('equal')
    plt.savefig(ROOT / "results" / "diagrams" / 'adoption_rate_overall.pdf')
    plt.show()


def calculate_adoption_rate_by_language(summaries):
    language_stats = defaultdict(lambda: {'total_repos': 0, 'adopted_repos': 0})

    for summary in summaries:
        language = summary.get('language', 'Unknown')
        language_stats[language]['total_repos'] += 1
        if summary.get('cc_adoption_date') is not None:
            language_stats[language]['adopted_repos'] += 1

    adoption_rates = {
        language: (stats['adopted_repos'] / stats['total_repos'] * 100) if stats['total_repos'] > 0 else 0
        for language, stats in language_stats.items()
    }

    for language, rate in adoption_rates.items():
        print(f"Sprache: {language}")
        print(f"  Gesamtzahl der Repositories: {language_stats[language]['total_repos']}")
        print(f"  Repositories mit CC-Nutzung: {language_stats[language]['adopted_repos']}")
        print(f"  Adoptionsrate: {rate:.2f}%")
        print('-' * 40)

    sorted_adoption_rates = dict(sorted(adoption_rates.items(), key=lambda item: item[1], reverse=True))

    plot_adoption_rate_by_language(sorted_adoption_rates)

    return adoption_rates


def plot_adoption_rate_by_language(adoption_rates):
    languages = list(adoption_rates.keys())
    rates = [adoption_rates[lang] for lang in languages]

    plt.figure(figsize=(12, 6))
    bars = plt.bar(languages, rates, color='skyblue')
    plt.xlabel('Programmiersprache')
    plt.ylabel('Adoptionsrate (%)')
    plt.title('Adoptionsrate von Conventional Commits nach Programmiersprache')

    # Prozentwerte über den Balken anzeigen
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, height, f'{height:.1f}%', ha='center', va='bottom')

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(ROOT / "results" / "diagrams" / f'adoption_rate_by_language.png')
    plt.show()


def calculate_adoption_rate_by_size(summaries, file_path):
    # Collect sizes from summaries
    sizes = [s.get('size', 0) for s in summaries]
    sizes = sorted(sizes)

    # Determine percentiles for size categories (e.g., 0-5%, 5-10%, ..., 95-100%)
    percentiles = np.percentile(sizes, np.arange(0, 101, 5))

    # Define size categories
    size_categories = {}
    for i in range(len(percentiles) - 1):
        category_name = f'Category {i + 1}'
        size_categories[category_name] = {'min': percentiles[i], 'max': percentiles[i + 1]}

    # Initialize statistics dictionary
    size_stats = {k: {'total_repos': 0, 'adopted_repos': 0} for k in size_categories}

    # Assign repositories to size categories and accumulate stats
    for summary in summaries:
        size = summary.get('size', 0)
        adopted = summary.get('cc_adoption_date') is not None
        for category, bounds in size_categories.items():
            if bounds['min'] <= size <= bounds['max']:
                size_stats[category]['total_repos'] += 1
                if adopted:
                    size_stats[category]['adopted_repos'] += 1
                break  # Break after finding the correct category

    # Calculate adoption rates and standard errors
    adoption_rates = {}
    standard_errors = {}
    for category, stats in size_stats.items():
        if stats['total_repos'] > 0:
            rate = (stats['adopted_repos'] / stats['total_repos']) * 100
            adoption_rates[category] = rate
            # Standard error for proportion
            p = stats['adopted_repos'] / stats['total_repos']
            se = np.sqrt(p * (1 - p) / stats['total_repos']) * 100
            standard_errors[category] = se
        else:
            adoption_rates[category] = 0
            standard_errors[category] = 0

    # Print results
    for category, rate in adoption_rates.items():
        print(f"Size Category: {category}")
        print(f"  Total Repositories: {size_stats[category]['total_repos']}")
        print(f"  Repositories with CC Adoption: {size_stats[category]['adopted_repos']}")
        print(f"  Adoption Rate: {rate:.2f}%")
        print('-' * 40)

    # Perform Logistic Regression
    perform_logistic_regression(summaries, size_categories)

    # Plot the adoption rates with error bars
    plot_adoption_rate_by_size(adoption_rates, standard_errors, file_path)

    return adoption_rates, size_stats


def perform_logistic_regression(summaries, size_categories):
    # Prepare DataFrame
    data = []
    for summary in summaries:
        size = summary.get('size', 0)
        adopted = int(summary.get('cc_adoption_date') is not None)
        # Determine size category as ordinal variable
        for i, (category, bounds) in enumerate(size_categories.items(), start=1):
            if bounds['min'] <= size <= bounds['max']:
                size_cat = i  # Ordinal encoding
                break
        else:
            size_cat = 0  # For any sizes not fitting into categories

        data.append({'size_category': size_cat, 'adopted': adopted})

    df = pd.DataFrame(data)

    # Remove any entries with size_category = 0 if any
    df = df[df['size_category'] > 0]

    # Define the independent variable with a constant for intercept
    X = sm.add_constant(df['size_category'])
    y = df['adopted']

    # Fit the logistic regression model
    model = sm.Logit(y, X)
    result = model.fit(disp=0)

    print("Logistische Regressionsergebnisse:")
    print(result.summary())
    print('-' * 40)

    # Interpret the coefficient
    coef = result.params['size_category']
    p_value = result.pvalues['size_category']
    odds_ratio = np.exp(coef)

    if p_value < 0.05:
        significance = "signifikant"
    else:
        significance = "nicht signifikant"

    print(
        f"Der Koeffizient für die Projektgröße-Kategorie beträgt {coef:.4f}, was einem Odds-Ratio von {odds_ratio:.4f} entspricht.")
    print(f"Der p-Wert ist {p_value:.4f}, was bedeutet, dass der Zusammenhang {significance} ist.")
    print('-' * 40)


def plot_adoption_rate_by_size(adoption_rates, file_path):
    categories = list(adoption_rates.keys())
    rates = [adoption_rates[cat] for cat in categories]

    plt.figure(figsize=(6.202, 4.652))
    bars = plt.barplot(categories, rates, capsize=5, color='skyblue', edgecolor='black')
    plt.xlabel('Projektgröße Kategorie (Quartile)')
    plt.ylabel('Adoptionsrate (%)')
    plt.title('Adoptionsrate von Conventional Commits nach Projektgröße')
    plt.ylim(0, 100)

    # Anzeige der Prozentwerte über den Balken
    for bar, rate in zip(bars, rates):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, height, f'{rate:.1f}%', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig(PLOTS / file_path)
    plt.show()


def calculate_adoption_rate_by_project_type(summaries, file_path):
    # Initialize statistics dictionary
    owner_stats = defaultdict(lambda: {'total_repos': 0, 'adopted_repos': 0})

    # Assign repositories to owner types and accumulate stats
    for summary in summaries:
        owner_type = summary.get('owner', 'Unknown')
        owner_type = owner_type if owner_type else 'Unknown'  # Handle empty strings
        adopted = summary.get('cc_adoption_date') is not None

        owner_stats[owner_type]['total_repos'] += 1
        if adopted:
            owner_stats[owner_type]['adopted_repos'] += 1

    # Calculate adoption rates
    adoption_rates = {
        owner_type: (stats['adopted_repos'] / stats['total_repos'] * 100) if stats['total_repos'] > 0 else 0
        for owner_type, stats in owner_stats.items()
    }

    # Print results
    for owner_type, rate in adoption_rates.items():
        print(f"Owner Type: {owner_type}")
        print(f"  Total Repositories: {owner_stats[owner_type]['total_repos']}")
        print(f"  Repositories with CC Adoption: {owner_stats[owner_type]['adopted_repos']}")
        print(f"  Adoption Rate: {rate:.2f}%")
        print('-' * 40)

    # Plot the adoption rates
    plot_adoption_rate_by_project_type(adoption_rates, file_path)


def plot_adoption_rate_by_project_type(adoption_rates, file_path):
    project_owner_types = list(adoption_rates.keys())
    rates = [adoption_rates[owner] for owner in project_owner_types]

    data = pd.DataFrame({
        'Project Owner Type': project_owner_types,
        'Adoption Rate (%)': rates
    })

    # Adjust font settings for LaTeX compatibility
    plt.rc('font', size=10)  # Standard font size
    plt.rc('axes', titlesize=12)  # Title font size
    plt.rc('axes', labelsize=10)  # Axis labels font size
    plt.rc('xtick', labelsize=8)  # X-axis tick labels font size
    plt.rc('ytick', labelsize=8)  # Y-axis tick labels font size
    plt.rc('legend', fontsize=8)  # Legend font size
    plt.rc('font', family='serif')  # Use a serif font for LaTeX compatibility

    plt.figure(figsize=(3.101, 2.326))
    ax = sns.barplot(x='Project Owner Type', y='Adoption Rate (%)', data=data, color='skyblue', ci=None)
    ax.set_xlabel('')
    ax.set_ylabel('')
    plt.ylim(0, max(rates) + 5)

    # Display percentage values above bars
    for p in ax.patches:
        height = p.get_height()
        ax.text(
            p.get_x() + p.get_width() / 2.,
            height + 0.5,
            '{:1.1f}%'.format(height),
            ha='center', va='bottom'
        )

    plt.tight_layout()
    plt.savefig(PLOTS / file_path)
    plt.show()


def clean_date_string(date_str):
    # If the date string ends with '+00:00Z', remove the 'Z'
    if date_str.endswith('+00:00Z'):
        date_str = date_str[:-1]  # Remove the trailing 'Z'
    # If the date string ends with 'Z' and contains a time zone offset, remove the 'Z'
    elif '+' in date_str and date_str.endswith('Z'):
        date_str = date_str[:-1]
    # If the date string ends with 'Z' and no time zone offset, keep it as is
    # If the date string contains '+00:00Z' in the middle, remove the 'Z'
    elif '+00:00Z' in date_str:
        date_str = date_str.replace('+00:00Z', '+00:00')
    return date_str


def calculate_adoption_rate_by_age(summaries, file_path):
    """
    Calculates the adoption rate of Conventional Commits by project age category and plots a bar chart.

    Parameters:
    - summaries (list of dict): List containing repository summaries with 'created_at' and 'cc_adoption_date' fields.
    - file_path (str): Path (including filename) to save the generated plot.
    """
    current_date = datetime.now(timezone.utc)
    ages = []
    data = []

    # Calculate ages of repositories and collect them
    for summary in summaries:
        created_at_str = summary.get('created_at', '')
        if not created_at_str:
            continue
        created_at_str = clean_date_string(created_at_str)
        try:
            created_at = parser.parse(created_at_str)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            else:
                created_at = created_at.astimezone(timezone.utc)
        except (ValueError, OverflowError) as e:
            print(f"Error parsing date '{created_at_str}': {e}")
            continue
        age = (current_date - created_at).days / 365.25  # Age in years
        ages.append(age)

    if not ages:
        print("No valid age data to process.")
        return

    ages = sorted(ages)

    # Determine quintiles for age categories
    quintiles = np.percentile(ages, [20, 40, 60, 80])

    # Define age categories with age ranges
    age_categories = {
        'New': {'min_age': 0, 'max_age': quintiles[0]},
        'Recent': {'min_age': quintiles[0], 'max_age': quintiles[1]},
        'Intermediate': {'min_age': quintiles[1], 'max_age': quintiles[2]},
        'Mature': {'min_age': quintiles[2], 'max_age': quintiles[3]},
        'Established': {'min_age': quintiles[3], 'max_age': max(ages)}
    }

    # Calculate date ranges for each category
    category_date_ranges = {}
    for category, bounds in age_categories.items():
        min_age = bounds['min_age']
        max_age = bounds['max_age']

        # Convert ages back to dates
        max_date = current_date - timedelta(days=min_age * 365.25)
        min_date = current_date - timedelta(days=max_age * 365.25)

        # Format dates
        min_date_str = min_date.strftime('%Y-%m-%d')
        max_date_str = max_date.strftime('%Y-%m-%d')

        category_date_ranges[category] = {'min_date': min_date_str, 'max_date': max_date_str}

    # Assign repositories to age categories and collect data for the bar plot
    for summary in summaries:
        created_at_str = summary.get('created_at', '')
        if not created_at_str:
            continue
        created_at_str = clean_date_string(created_at_str)
        try:
            created_at = parser.parse(created_at_str)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            else:
                created_at = created_at.astimezone(timezone.utc)
        except (ValueError, OverflowError) as e:
            print(f"Error parsing date '{created_at_str}': {e}")
            continue
        age = (current_date - created_at).days / 365.25
        adopted = summary.get('cc_adoption_date') is not None
        category = None
        for cat, bounds in age_categories.items():
            if bounds['min_age'] <= age <= bounds['max_age']:
                category = cat
                break
        if category:
            data.append({
                'Category': category,
                'Adopted': 'Adopted' if adopted else 'Not Adopted'
            })

    df = pd.DataFrame(data)

    if df.empty:
        print("No data available for plotting.")
        return

    # Create labels with date ranges
    def create_label(category):
        date_range = category_date_ranges[category]
        return f"{category}\n({date_range['min_date']} \n- {date_range['max_date']})"

    df['Category with Date'] = df['Category'].apply(create_label)

    # Define the order of categories
    category_order = ['New', 'Recent', 'Intermediate', 'Mature', 'Established']
    ordered_labels = [create_label(cat) for cat in category_order]

    # Calculate Adoption Rates
    adoption_rates = df.groupby('Category with Date')['Adopted'].value_counts().unstack().fillna(0)
    adoption_rates['Adoption Rate (%)'] = (adoption_rates.get('Adopted', 0) /
                                           (adoption_rates.get('Adopted', 0) + adoption_rates.get('Not Adopted',
                                                                                                  0))) * 100
    adoption_rates = adoption_rates.reset_index()

    # Create the Bar Plot with Seaborn
    plt.figure(figsize=(6.202, 4.652))  # Increased figure size for better readability
    bar_plot = sns.barplot(
        x='Category with Date',
        y='Adoption Rate (%)',
        data=adoption_rates,
        order=ordered_labels,
        palette='Blues_d'
    )

    # Adjust font settings for LaTeX compatibility
    plt.rc('font', size=10)  # Standard font size
    plt.rc('axes', titlesize=12)  # Title font size
    plt.rc('axes', labelsize=10)  # Axis labels font size
    plt.rc('xtick', labelsize=8)  # X-axis tick labels font size
    plt.rc('ytick', labelsize=8)  # Y-axis tick labels font size
    plt.rc('legend', fontsize=8)  # Legend font size
    plt.rc('font', family='serif')  # Use a serif font for LaTeX compatibility

    # plt.xlabel('Project Age Category', fontsize=14)  # Increased font size for x-axis label
    # plt.ylabel('Adoption Rate (%)', fontsize=14)     # Increased font size for y-axis label
    # plt.title('Application Trend of CC by Project Age', fontsize=16)  # Increased font size for title

    # Correctly display percentage values above the bars
    for p in bar_plot.patches:
        height = p.get_height()
        bar_plot.annotate(
            f"{height:.2f}%",
            (p.get_x() + p.get_width() / 2., height + 1),  # Position slightly above the bar
            ha='center',
            va='bottom',  # Increased font size for annotations
            color='black'
        )
        # Increased font size for y-axis tick labels
    max_y_value = adoption_rates['Adoption Rate (%)'].max()
    plt.ylim(0, max_y_value * 1.1)
    plt.tight_layout()

    bar_plot.set_xlabel('')
    bar_plot.set_ylabel('')

    # Save and display the plot
    plt.savefig(PLOTS / file_path)
    plt.show()


def categorize_contributors(author_commit_counts):
    # Sort authors by commit count descending
    sorted_authors = sorted(author_commit_counts.items(), key=lambda x: x[1], reverse=True)
    total_commits = sum(author_commit_counts.values())

    core_devs = []
    active_contributors = []
    occasional_contributors = []
    one_time_contributors = []

    cumulative_commits = 0
    for author, count in sorted_authors:
        cumulative_commits += count
        commit_percentage = cumulative_commits / total_commits * 100

        if commit_percentage <= 80:
            core_devs.append(author)
        elif count > 10:
            active_contributors.append(author)
        elif count > 1:
            occasional_contributors.append(author)
        else:
            one_time_contributors.append(author)

    return {
        'Core Developers': core_devs,
        'Active Contributors': active_contributors,
        'Occasional Contributors': occasional_contributors,
        'One-time Contributors': one_time_contributors
    }


def analyze_contributor_consistency(summaries, results_dir):
    # Initialize overall accumulators
    overall_cc_usage = {'Before CC Adoption': defaultdict(lambda: {'total_commits': 0, 'cc_commits': 0}),
                        'After CC Adoption': defaultdict(lambda: {'total_commits': 0, 'cc_commits': 0})}
    contributor_categories_set = set()
    total_commits_per_contributor_type = defaultdict(int)
    total_commits_all = 0  # Total commits across all repositories

    # Iterate over repositories
    for summary in summaries:
        repo_id = summary.get('id')
        cc_adoption_date_str = summary.get('cc_adoption_date')
        language = summary.get('language', 'Unknown')

        # Load commit data
        json_file_path = RESULTS / f"{repo_id}.json"
        if not json_file_path.exists():
            continue  # Skip if commit data is not available

        data = load_from_json(json_file_path)
        commits = data.get('commits', [])

        # Separate commits before and after CC adoption
        if cc_adoption_date_str:
            cc_adoption_date = datetime.strptime(cc_adoption_date_str, "%Y-%m-%d")
            commits_before = [c for c in commits if
                              datetime.strptime(c['committed_datetime'], "%Y-%m-%dT%H:%M:%S") < cc_adoption_date]
            commits_after = [c for c in commits if
                             datetime.strptime(c['committed_datetime'], "%Y-%m-%dT%H:%M:%S") >= cc_adoption_date]
        else:
            commits_before = commits
            commits_after = []

        # Analyze contributors
        for period, period_commits in [('Before CC Adoption', commits_before), ('After CC Adoption', commits_after)]:
            if not period_commits:
                continue  # Skip if no commits in this period

            author_commit_counts = Counter(c['author'] for c in period_commits)
            total_commits = sum(author_commit_counts.values())
            total_commits_all += total_commits  # Update total commits across all repositories

            # Categorize contributors
            contributor_categories = categorize_contributors(author_commit_counts)
            contributor_categories_set.update(contributor_categories.keys())

            # Analyze CC usage per contributor type
            for category, authors in contributor_categories.items():
                category_commits = [c for c in period_commits if c['author'] in authors]
                cc_commits = [c for c in category_commits if c.get('is_conventional')]

                # Update overall counts
                overall_cc_usage[period][category]['total_commits'] += len(category_commits)
                overall_cc_usage[period][category]['cc_commits'] += len(cc_commits)

                # Update total commits per contributor type
                total_commits_per_contributor_type[category] += len(category_commits)

    # After processing all repositories, compute overall CC usage rates
    # and plot the aggregated data
    plot_overall_contributor_cc_usage(overall_cc_usage, contributor_categories_set, total_commits_per_contributor_type,
                                      total_commits_all)


def plot_overall_contributor_cc_usage(overall_cc_usage, contributor_categories_set, total_commits_per_contributor_type,
                                      total_commits_all):
    categories = list(contributor_categories_set)
    periods = ['Before CC Adoption', 'After CC Adoption']
    usage_rates = {period: [] for period in periods}
    commit_percentage_per_category = []

    for category in categories:
        total_commits_category = total_commits_per_contributor_type.get(category, 0)
        percentage_of_total_commits = (total_commits_category / total_commits_all * 100) if total_commits_all > 0 else 0
        commit_percentage_per_category.append(percentage_of_total_commits)

        for period in periods:
            stats = overall_cc_usage[period].get(category, {'total_commits': 0, 'cc_commits': 0})
            total_commits = stats['total_commits']
            cc_commits = stats['cc_commits']
            cc_usage_rate = (cc_commits / total_commits * 100) if total_commits > 0 else 0
            usage_rates[period].append(cc_usage_rate)

    x = np.arange(len(categories))  # Label locations
    width = 0.35  # Width of the bars

    fig, ax1 = plt.subplots(figsize=(12, 6))

    rects1 = ax1.bar(x - width / 2, usage_rates['Before CC Adoption'], width, label='Before CC Adoption')
    rects2 = ax1.bar(x + width / 2, usage_rates['After CC Adoption'], width, label='After CC Adoption')

    ax1.set_ylabel('CC Usage Rate (%)')
    ax1.set_xlabel('Contributor Type')
    ax1.set_title('CC Usage Rate by Contributor Type Before and After CC Adoption')
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories)
    ax1.legend()

    # Attach text labels above each bar
    def autolabel(rects):
        """Attach a text label above each bar displaying its height"""
        for rect in rects:
            height = rect.get_height()
            ax1.annotate(f'{height:.1f}%',
                         xy=(rect.get_x() + rect.get_width() / 2, height),
                         xytext=(0, 3),  # Offset text by 3 points vertically
                         textcoords="offset points",
                         ha='center', va='bottom')

    autolabel(rects1)
    autolabel(rects2)

    # Attach percentage of total commits below each group of bars
    for i in range(len(categories)):
        total_pct = commit_percentage_per_category[i]
        max_height = max(usage_rates['Before CC Adoption'][i], usage_rates['After CC Adoption'][i])
        ax1.annotate(f'{total_pct:.1f}% of commits',
                     xy=(x[i], max_height - 5),  # Set position below the bar
                     xytext=(0, 0),
                     textcoords="offset points",
                     ha='center', va='top', fontsize=9, color='blue')  # Adjust vertical alignment

    fig.tight_layout()
    plt.savefig(PLOTS/ 'cc_usage_by_contributor_overall.png')
    plt.show()


def plot_contributor_distribution(contributor_counts, repo_name, period):
    categories = list(contributor_counts.keys())
    counts = [len(contributor_counts[cat]) for cat in categories]

    plt.figure(figsize=(8, 6))
    bars = plt.bar(categories, counts, color='skyblue')
    plt.xlabel('Contributor Type')
    plt.ylabel('Number of Contributors')
    plt.title(f'Contributor Distribution in {repo_name} ({period})')

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, height, str(int(height)), ha='center', va='bottom')

    plt.tight_layout()
    plt.show()


def aggregate_commit_types_by_language(summaries, string):
    language_type_distribution = defaultdict(lambda: Counter())

    for summary in summaries:
        language = summary.get('language', 'Unknown')
        type_distribution = summary.get(string, {})
        language_type_distribution[language].update(type_distribution)

    # For each language, plot the distribution
    for language, type_counter in language_type_distribution.items():
        print(f"Commit Type Distribution for {language}:")
        for ctype, count in type_counter.items():
            print(f"{ctype}: {count}")

        plot_commit_type_distribution(type_counter, language, string)


def plot_commit_type_distribution(type_counter, language, string):
    # Sort the types by frequency
    types = list(type_counter.keys())
    counts = [type_counter[ctype] for ctype in types]
    data = sorted(zip(counts, types), reverse=True)
    counts_sorted, types_sorted = zip(*data[:30])  # Limit to top 30 types

    plt.figure(figsize=(10, 6))
    bars = plt.bar(types_sorted, counts_sorted, color='purple')
    plt.xlabel('Commit Type')
    plt.ylabel('Count')
    plt.title(f'Commit Type Distribution for {language}')
    plt.xticks(rotation=45)

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, int(yval), ha='center', va='bottom', fontsize=7)

    plt.tight_layout()
    plt.savefig(ROOT / "results" / "diagrams" / f'{language}_{string}.png')
    plt.show()


if __name__ == "__main__":
    logger = set_logging()

    RESULTS.mkdir(exist_ok=True)
    logging.info(f"Lade Daten aus {YAML}")
    repos = load_dataset()
    logging.info(f"Daten geladen: {len(repos)} Repositories")

    # i = 0
    #
    # for repo_data in repos:
    #     i += 1
    #     process_repository(repo_data, RESULTS)
    #     logger.counter(f"Processed {i} repos")

    # Laden der Zusammenfassungen
    logging.info(f"Lade Zusammenfassungen aus {RESULTS}")
    summaries = load_analysis_summaries(RESULTS)
    logging.info(f"Anzahl der analysierten Repos: {len(summaries)}")

    logging.info(f"Extrahiere CC-Summaries")
    summaries_adopted = [s for s in summaries if s.get('cc_adoption_date') is not None]
    summaries_consistent = [s for s in summaries if s.get("is_consistently_conventional")]
    summaries_only_adopted = [s for s in summaries if
                              s.get('cc_adoption_date') is not None and not s.get("is_consistently_conventional")]
    logging.info(f"Anzahl der Repos mit CC-Adoption und konsistentem CC-Verhalten: {len(summaries_consistent)}")
    logging.info(f"Anzahl der Repos mit CC-Adoption: {len(summaries_adopted)}")
    logging.info(
        f"Anzahl der Repos mit CC-Adoption, aber nicht konsistentem CC-Verhalten: {len(summaries_only_adopted)}")

    # Data for the pie chart
    labels = ['Overall CC-Consistent', 'CC-Adoption', 'No Adoption']
    sizes = [len(summaries_consistent), len(summaries_only_adopted), len(summaries) - len(summaries_adopted)]
    colors = ['#ff9999', '#66b3ff', '#99ff99']

    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, colors=colors,
            autopct='%1.1f%%')
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    plt.title('Adoption Status Distribution')
    plt.show()

    # TODO:  1.1 Overall Adoption Rate - Alle Repos
    # Berechnung der Adoptionsrate
    logging.info(f"Berechne Adoptionsrate")
    calculate_adoption_rate(summaries)

    # 1.1.1 Adoption Rate by Programming Language
    logging.info(f"Berechne Adoptionsrate nach Programmiersprache")
    calculate_adoption_rate_by_language(summaries)

    # 1.1.2 Adoption Rate by Project Size
    logging.info(f"Berechne Adoptionsrate nach Projektgröße")
    calculate_adoption_rate_by_size(summaries)

    # 1.1.3 Adoption Rate by Community Activity ???

    # 1.1.4 Adoption Rate by Project Age
    logging.info(f"Berechne Adoptionsrate nach Projektalter")
    calculate_adoption_rate_by_age(summaries)

    # 1.1.5 Adoption Rate by Project Type
    calculate_adoption_rate_by_project_type(summaries)

    # TODO: RQ1.2 Consistency - Wer nutzt CC? - auf CC und Non-CC Repos anwenden
    # 1.2.1 Consistency auf Entwicklerebene
    # Aufschlüsseln der Contibutor in 4 Gruppen:
    # - Core developers
    # - Active contributors
    # - Occasional contributors
    # - One-time contributors
    # Verteilung der Contributor-Typen plotten
    # Verteilung der Commits nach Contributor-Typen plotten
    # Vergleich der Verteilung der Commits nach Contributor-Typen vor und nach der Adoption
    analyze_contributor_consistency(summaries_adopted, results_dir=RESULTS)

    # 1.2.2 Consistency über die Zeit - mal schauen

    # Ergebnis z.B.
    # Nach der Adoption von CC nutzen zu 90% Core Developers CC,
    # One-time Contributors nutzen nur in 10% der Fälle CC

    # TODO 1.3 Commit Type Distribution - nur auf Repos mit CC anwenden
    # 1.3.1 Commit Type Distribution -- CC-Types
    # - total
    aggregate_commit_types(summaries_adopted, 'cc_type_distribution')
    aggregate_commit_types(summaries_adopted, 'custom_type_distribution')
    # - by Programming Language
    aggregate_commit_types_by_language(summaries_adopted, 'cc_type_distribution')
    aggregate_commit_types_by_language(summaries_adopted, 'custom_type_distribution')

# - by Contributor Type
# 1.3.2 Commit Type Distribution -- Custom-Types
# - total - manuelle Auswertung der ersten ... types
# - by Programming Language
# - by Contributor Type
# 1.3.3 Exkurs: custom-types mit ChatGPT API analysieren und kategorisieren - weiterführende Forschung

# TODO 1.4 Impact on Project Management --> ggf. weiterführende Forschung
# 1.4.1 Effekt auf Effort Estimation
# 1.4.2 Effekt auf Resource Allocation
# 1.4.3 Effekt auf Projektmanagement-Tasks
