import datetime
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from dateutil import parser
from constants import COMMIT_ANALYSIS_RESULTS, PLOTS, RESULTS
from tabulate import tabulate

# Define a consistent green color palette
colors = ['#e6f4e6', '#c3e6c3', '#a1d8a1', '#7eca7e', '#5cbd5c', '#4da64d', '#3d8c3d']

# Set global plot settings for LaTeX compatibility and consistency
plt.rcParams.update({
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 10,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    'font.family': 'serif',
    'text.usetex': False  # Set to True if using LaTeX rendering
})


def analyze_rq1(repos, summaries, commits, dataset):
    """
    Performs analysis related to Research Question 1.
    """
    # Plot CCP over all Repos and CC-Repos
    plot_ccp(repos, 'cc_over_time.pdf')

    # Plot adoption rate by language
    plot_adoption_rate_by_language(summaries, 'adoption_rate_by_language.pdf')

    # Calculate adoption rate by project type
    calculate_adoption_rate_by_project_type(summaries, "adoption_rate_by_project_type.pdf")

    # Calculate adoption rate by age
    calculate_adoption_rate_by_age(summaries, 'adoption_rate_by_project_age.pdf')

    # Calculate adoption trends over time
    calculate_adoption_trends(summaries, "adoption_ratio_over_time.pdf")

    # Plot adoption rate by project size
    plot_cc_adoption_by_project_size(summaries, "adoption_rate_by_project_size.pdf")

    # Plot commit types impact on codebase metrics
    plot_commit_types_impact_on_codebase_metrics_bar(commits, 'commit_types_impact_on_codebase_metrics_bar.pdf')

    # Compare cc indication and adoption date
    classification_matrix = compare_cc_indication(repos)

    # Analyze repository characteristics
    repo_characteristics_df = get_repository_characteristics(repos)
    correlations = calculate_correlations(repo_characteristics_df)
    adoption_by_language = analyze_language_influence(repo_characteristics_df)
    print(adoption_by_language)

    # Analyze and plot commit types distribution
    analyze_commit_types_distribution(repos)

    # Compile overall results
    compile_overall_results(repos, dataset, classification_matrix, correlations)


def calculate_ccp(repos):
    """
    Loads all commits from JSON files and filters out repositories without a cc_adoption_date.

    Parameters:
        repos (list of dict): List of repository data.

    Returns:
        pd.DataFrame: DataFrame with commits from repositories with a valid cc_adoption_date.
    """
    commits_cc = 0
    commits_custom = 0
    len_commits = 0

    cc_commits_cc = 0
    cc_commits_custom = 0
    len_cc_commits = 0

    cc_in_non_cc_repos = 0
    custom_in_non_cc_repos = 0

    for repo in repos:

        commits = repo.get('commits', [])
        adoption_date = repo.get('analysis_summary').get('cc_adoption_date')

        commits_cc += len([commit for commit in commits if commit.get('custom_type') is not None])
        commits_custom += len([commit for commit in commits if commit.get('cc_type') is not None])
        len_commits += len(commits)

        if adoption_date:
            cc_commits = [commit for commit in commits if adoption_date is not None]
            cc_commits_cc += len([commit for commit in cc_commits if commit.get('cc_type') is not None])
            cc_commits_custom += len([commit for commit in cc_commits if commit.get('custom_type') is not None])
            len_cc_commits += len(cc_commits)
        else:
            cc_in_non_cc_repos += len([commit for commit in commits if commit.get('cc_type') is not None])
            custom_in_non_cc_repos += len([commit for commit in commits if commit.get('custom_type') is not None])


    total_cc_commits_rate = commits_cc / len_commits * 100
    total_custom_commits_rate = commits_custom / len_commits * 100
    cc_commits_rate = cc_commits_cc / len_cc_commits * 100
    custom_commits_rate = cc_commits_custom / len_cc_commits * 100
    total_cc_in_non_cc_repos_rate = cc_in_non_cc_repos / len_commits * 100
    total_custom_in_non_cc_repos_rate = custom_in_non_cc_repos / len_commits * 100

    return total_cc_commits_rate, total_custom_commits_rate, cc_commits_rate, custom_commits_rate, total_cc_in_non_cc_repos_rate, total_custom_in_non_cc_repos_rate


def plot_ccp(repos, file):
    total_cc_commits_rate, total_custom_commits_rate, cc_commits_rate, custom_commits_rate, total_cc_in_non_cc_repos_rate, total_custom_in_non_cc_repos_rate = calculate_ccp(repos)

    data = pd.DataFrame({
        'Category': ['CC-Type Commits \noverall', 'Custom-Type Commits \noverall', 'CC-Type Commits \nin CC-Repos',
                     'Custom-Type Commits \nin CC-Repos', 'CC-Type Commits \nin non-CC-Repos', 'Custom-Type Commits \nin non-CC-Repos'],
        'CCP': [round(total_cc_commits_rate, 2), round(total_custom_commits_rate, 2), round(cc_commits_rate, 2),
                round(custom_commits_rate, 2), round(total_cc_in_non_cc_repos_rate, 2), round(total_custom_in_non_cc_repos_rate, 2)]
    })

    # Erstellen des Barplots
    plt.figure(figsize=(6.202, 3.000))
    ax = sns.barplot(x='Category', y='CCP', data=data, color=colors[6])
    ax.bar_label(ax.containers[0], fontsize=10)

    # Achsen und Titel
    plt.ylabel('Average CCP (%)')
    plt.ylim(0, 100)  # Annahme, dass der CCP zwischen 0 und 100 liegt
    # Anzeige des Plots

    plt.xticks(fontsize=5)
    plt.tight_layout()
    plt.savefig(PLOTS / file)
    plt.close()


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

    # Escape LaTeX special characters
    df['Language'] = df['Language'].apply(escape_latex)

    plt.figure(figsize=(6.202, 4.652))
    ax = sns.barplot(data=df, x='Adoption Rate (%)', y='Language', color=colors[4])
    ax.set_xlabel('')
    ax.set_ylabel('')
    plt.tight_layout()
    plt.savefig(PLOTS / file_path)
    plt.close()


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

    # Plot the adoption rates
    plot_adoption_rate_by_project_type(adoption_rates, file_path)


def plot_adoption_rate_by_project_type(adoption_rates, file_path):
    project_owner_types = list(adoption_rates.keys())
    rates = [adoption_rates[owner] for owner in project_owner_types]

    data = pd.DataFrame({
        'Project Owner Type': project_owner_types,
        'Adoption Rate (%)': rates
    })

    # Create the bar plot
    plt.figure(figsize=(3.101, 2.326))
    ax = sns.barplot(x='Project Owner Type', y='Adoption Rate (%)', data=data, color=colors[4], ci=None)
    ax.set_xlabel('')
    ax.set_ylabel('')
    plt.ylim(0, max(rates) + 5)

    # Display percentage values above bars
    for p in ax.patches:
        height = p.get_height()
        ax.text(
            p.get_x() + p.get_width() / 2.,
            height + 0.5,
            f'{height:.1f}%',
            ha='center', va='bottom'
        )

    plt.tight_layout()
    plt.savefig(PLOTS / file_path)
    plt.close()


def clean_date_string(date_str):
    # Handle specific date string formats
    if date_str.endswith('+00:00Z'):
        date_str = date_str[:-1]  # Remove the trailing 'Z'
    elif '+' in date_str and date_str.endswith('Z'):
        date_str = date_str[:-1]
    elif '+00:00Z' in date_str:
        date_str = date_str.replace('+00:00Z', '+00:00')
    return date_str


def calculate_adoption_rate_by_age(summaries, file_path):
    """
    Calculates the adoption rate of Conventional Commits by project age category and plots a bar chart.
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

    # Determine groups for age categories
    groups = np.percentile(ages, [20, 40, 60, 80])

    # Define age categories with age ranges
    age_categories = {
        'New': {'min_age': 0, 'max_age': groups[0]},
        'Recent': {'min_age': groups[0], 'max_age': groups[1]},
        'Intermediate': {'min_age': groups[1], 'max_age': groups[2]},
        'Mature': {'min_age': groups[2], 'max_age': groups[3]},
        'Established': {'min_age': groups[3], 'max_age': max(ages)}
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
        return f"{category}\n({date_range['min_date']} - \n{date_range['max_date']})"

    df['Category with Date'] = df['Category'].apply(create_label)

    # Define the order of categories
    category_order = ['New', 'Recent', 'Intermediate', 'Mature', 'Established']
    ordered_labels = [create_label(cat) for cat in category_order]

    # Calculate Adoption Rates
    adoption_counts = df.groupby('Category with Date')['Adopted'].value_counts().unstack().fillna(0)
    adoption_rates = (adoption_counts.get('Adopted', 0) /
                      (adoption_counts.get('Adopted', 0) + adoption_counts.get('Not Adopted', 0))) * 100
    adoption_rates = adoption_rates.reindex(ordered_labels)

    # Create the bar plot
    plt.figure(figsize=(6.202, 4.652))
    ax = sns.barplot(
        x=adoption_rates.index,
        y=adoption_rates.values,
        palette=colors[2:7]
    )
    plt.rc('xtick', labelsize=8)

    # Correctly display percentage values above the bars
    for p, rate in zip(ax.patches, adoption_rates.values):
        height = p.get_height()
        ax.annotate(
            f"{rate:.2f}%",
            (p.get_x() + p.get_width() / 2., height + 1),
            ha='center',
            va='bottom',
            color='black'
        )

    max_y_value = adoption_rates.max()
    plt.ylim(0, max_y_value * 1.1)
    ax.set_xlabel('')
    ax.set_ylabel('')
    plt.tight_layout()

    plt.savefig(PLOTS / file_path)
    plt.close()


def calculate_adoption_trends(summaries, file_path):
    adopted_by_year = defaultdict(int)
    existing_repos_by_year = defaultdict(int)

    current_year = datetime.now(timezone.utc).year

    for summary in summaries:
        created_at_str = summary.get('created_at', '')
        if not created_at_str:
            continue
        created_at = datetime.strptime(created_at_str[:10], "%Y-%m-%d").year
        cc_adoption_date_str = summary.get('cc_adoption_date')

        if cc_adoption_date_str:
            adoption_year = datetime.strptime(cc_adoption_date_str[:10], "%Y-%m-%d").year
            for year in range(created_at, current_year + 1):
                existing_repos_by_year[year] += 1
                if year >= adoption_year:
                    adopted_by_year[year] += 1
        else:
            for year in range(created_at, current_year + 1):
                existing_repos_by_year[year] += 1

    # Ensure all years are covered
    start_year = 2017
    end_year = current_year
    years = list(range(start_year, end_year + 1))

    # Calculate adoption ratio (percentage)
    adoption_ratio = [
        100 * adopted_by_year[year] / existing_repos_by_year[year] if existing_repos_by_year[year] > 0 else 0
        for year in years
    ]

    # Create the line plot
    plt.figure(figsize=(3.101, 2.326))
    plt.plot(years, adoption_ratio, marker='o', color=colors[6])
    plt.fill_between(years, adoption_ratio, color=colors[2], alpha=0.3)
    plt.xlabel('')
    plt.ylabel('')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(PLOTS / file_path)
    plt.close()


def plot_cc_adoption_by_project_size(summaries, file_path):
    """
    Calculates the adoption rate of Conventional Commits by project size and plots a bar chart.
    """
    # Create a DataFrame from the summaries
    df = pd.DataFrame(summaries)

    # Ensure 'size' column is valid
    if 'size' not in df.columns or df['size'].isnull().all():
        print("The 'size' column is not present or contains no valid values.")
        return

    # Clean the data
    df = df.dropna(subset=['size'])
    df = df[df['size'] >= 0]

    # Calculate quartiles
    quartiles = np.quantile(df['size'], [0.25, 0.5, 0.75])

    # Define size categories
    size_bins = [df['size'].min(), quartiles[0], quartiles[1], quartiles[2], df['size'].max()]
    size_labels = ['Small', 'Medium', 'Large', 'Very Large']

    df['Size Category'] = pd.cut(df['size'], bins=size_bins, labels=size_labels, include_lowest=True)

    # Determine CC adoption
    df['CC Adopted'] = df['cc_adoption_date'].notnull()

    # Calculate adoption rates
    adoption_rates = df.groupby('Size Category')['CC Adopted'].mean().reset_index()
    adoption_rates['Adoption Rate (%)'] = adoption_rates['CC Adopted'] * 100

    # Sort categories
    category_order = ['Small', 'Medium', 'Large', 'Very Large']
    adoption_rates['Size Category'] = pd.Categorical(adoption_rates['Size Category'], categories=category_order,
                                                     ordered=True)
    adoption_rates = adoption_rates.sort_values('Size Category')

    # Create the bar plot
    plt.figure(figsize=(6.202, 4.652))
    ax = sns.barplot(
        x='Size Category',
        y='Adoption Rate (%)',
        data=adoption_rates,
        palette=colors[2:6],
        order=category_order
    )
    ax.set_xlabel('')
    ax.set_ylabel('')
    plt.ylim(0, max(adoption_rates['Adoption Rate (%)']) + 5)

    # Display percentage values above bars
    for p in ax.patches:
        height = p.get_height()
        ax.text(
            p.get_x() + p.get_width() / 2.,
            height + 1,
            f'{height:.1f}%',
            ha='center', va='bottom'
        )

    plt.tight_layout()
    plt.savefig(PLOTS / file_path)
    plt.close()


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

    # Create DataFrame for plotting
    df = pd.DataFrame({
        'Contributor Type': categories * len(periods),
        'CC Usage Rate (%)': usage_rates['Before CC Adoption'] + usage_rates['After CC Adoption'],
        'Period': ['Before CC Adoption'] * len(categories) + ['After CC Adoption'] * len(categories)
    })

    # Create the grouped bar chart
    plt.figure(figsize=(6.202, 4.652))
    ax = sns.barplot(
        x='Contributor Type',
        y='CC Usage Rate (%)',
        hue='Period',
        data=df,
        palette=colors[2:4]
    )
    ax.set_xlabel('')
    ax.set_ylabel('')
    plt.legend(title='', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(PLOTS / 'cc_usage_by_contributor_overall.pdf')
    plt.close()


def plot_commit_types_impact_on_codebase_metrics_bar(commits, file_path, figsize=(6.202, 4.652)):
    """
    Plots a grouped bar chart showing Insertions and Deletions for each Commit Type.
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

    # Create the bar chart
    plt.figure(figsize=figsize)
    ax = sns.barplot(data=plot_df, x='Commit Type', y='Count', hue='Metric', palette='Set2')
    plt.legend(title='', loc='upper right', bbox_to_anchor=(1, 1), borderaxespad=0.5, frameon=True)
    ax.set_xlabel('')
    ax.set_ylabel('')
    plt.tight_layout()

    # Save the plot
    plt.savefig(PLOTS / file_path)
    plt.close()


def compare_cc_indication(repositories):
    """
    Compares cc_indication flag with actual CC implementation.
    Returns a matrix (DataFrame) of counts of discrepancies.
    """
    # Count occurrences using a Counter
    counts = Counter(
        (
            repo['analysis_summary']['cc_indication'],
            bool(repo['analysis_summary']['cc_adoption_date'])
        )
        for repo in repositories
    )

    # Prepare DataFrame matrix
    matrix = pd.DataFrame(
        [
            [counts[(True, True)], counts[(True, False)]],
            [counts[(False, True)], counts[(False, False)]]
        ],
        columns=['CC Adopted', 'CC Not Adopted'],
        index=['CC Indication: True', 'CC Indication: False']
    )

    return matrix


def get_repository_characteristics(repositories):
    """
    Collects repository characteristics into a DataFrame.
    """
    data = []
    for repo in repositories:
        analysis = repo['analysis_summary']
        data.append({
            'name': analysis['name'],
            'language': analysis['language'],
            'size': analysis['size'],
            'owner_type': analysis['owner'],
            'created_at': analysis['created_at'],
            'cc_adoption_date': analysis['cc_adoption_date'],
            'ccp': analysis.get('ccp', 0),
            'cc_indication': analysis['cc_indication'],
            'total_commits': analysis['total_commits'],
            'conventional_commits': analysis['conventional_commits'],
            'unconventional_commits': analysis['unconventional_commits']
        })
    df = pd.DataFrame(data)

    # Convert date strings to datetime objects
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['cc_adoption_date'] = pd.to_datetime(df['cc_adoption_date'])

    # Calculate repository age in days
    df['repo_age_days'] = (datetime.now() - df['created_at']).dt.days

    # Calculate CC adoption status
    df['has_adopted_cc'] = df['cc_adoption_date'].notnull().astype(int)

    return df


def calculate_correlations(df):
    """
    Calculates correlations between CC adoption and repository metrics.
    Returns a dictionary of correlations.
    """
    correlations = {}
    metrics = ['size', 'total_commits', 'repo_age_days']

    for metric in metrics:
        if df[metric].dtype not in ['float64', 'int64']:
            continue  # Skip non-numeric metrics

        correlation = df['has_adopted_cc'].corr(df[metric])
        correlations[metric] = correlation
        print(f"Correlation between CC adoption and {metric}: {correlation:.2f}")

    return correlations


def analyze_language_influence(df):
    """
    Analyzes whether certain programming languages have higher rates of CC adoption.
    """
    adoption_by_language = df.groupby('language')['cc_adoption_date'].apply(lambda x: x.notnull().mean())
    adoption_by_language = adoption_by_language.sort_values(ascending=False)
    return adoption_by_language


def analyze_commit_types_distribution(repositories):
    """
    Analyzes the distribution of standard CC types and custom types across repositories.
    """
    standard_types_counts = {}
    custom_types_counts = {}

    for repo in repositories:
        analysis = repo['analysis_summary']
        cc_types = analysis.get('cc_type_distribution', {})
        custom_types = analysis.get('custom_type_distribution', {})

        for ctype, count in cc_types.items():
            standard_types_counts[ctype] = standard_types_counts.get(ctype, 0) + count

        for ctype, count in custom_types.items():
            custom_types_counts[ctype] = custom_types_counts.get(ctype, 0) + count

    # Plot standard commit types
    standard_df = pd.DataFrame(list(standard_types_counts.items()), columns=['Commit Type', 'Count'])
    standard_df = standard_df.sort_values(by='Count', ascending=False)

    plt.figure(figsize=(6.202, 4.652))
    ax = sns.barplot(x='Commit Type', y='Count', data=standard_df, palette=colors[2:7])

    # Rotate x-axis labels to avoid overlap
    plt.xticks(rotation=45)
    ax.set_xlabel('')
    ax.set_ylabel('')

    plt.tight_layout()
    plt.savefig(PLOTS / 'cc_type_distribution.pdf')
    plt.close()

    # Plot custom commit types (Top 20)
    custom_df = pd.DataFrame(list(custom_types_counts.items()), columns=['Custom Type', 'Count'])
    custom_df = custom_df.sort_values(by='Count', ascending=False).head(20)

    plt.figure(figsize=(6.202, 4.652))
    ax = sns.barplot(x='Custom Type', y='Count', data=custom_df, palette=colors[2:7])

    plt.xticks(rotation=45)
    ax.set_xlabel('')
    ax.set_ylabel('')

    plt.tight_layout()
    plt.savefig(PLOTS / 'custom_type_distribution.pdf')
    plt.close()


def extract_contributors_from_commits(commits):
    """Extract unique contributors based on commit authors."""
    contributors = {commit.get('author') for commit in commits if commit.get('author')}
    return len(contributors)


def calculate_project_age(created_at):
    """Calculate the age of a project based on the creation date with timezone info."""
    created_date = datetime.fromisoformat(created_at.replace("Z", ""))
    today = datetime.now(timezone.utc)
    age_years = (today - created_date).days / 365.25
    return age_years


def load_repo_data_by_id(repo_id):
    """Load commit data for a specific repository by ID."""
    repo_file = COMMIT_ANALYSIS_RESULTS / f"{repo_id}.json"
    if not repo_file.is_file():
        print(f"Repo file {repo_file} not found for repository {repo_id}. Skipping.")
        return None
    with open(repo_file, 'r', encoding='utf-8') as rf:
        return json.load(rf)


def gather_repo_data(repos_data):
    """Collect data for each repository and return it as a DataFrame."""
    data = []
    owner_stats = defaultdict(lambda: {'num_projects': 0, 'total_contributors': 0, 'total_stars': 0, 'age': 0})
    language_stats = defaultdict(lambda: {'num_projects': 0, 'total_contributors': 0, 'total_stars': 0, 'age': 0})

    for repo in repos_data:
        repo_data = load_repo_data_by_id(repo.get('id'))
        if repo_data is None:
            continue

        language = repo_data.get('analysis_summary', {}).get('language', 'Unknown')
        stars = repo.get('stargazers_count', 0)
        size = repo.get('size', 0)
        owner = repo.get('owner', 'Unknown')
        total_commits = repo_data.get('analysis_summary', {}).get('total_commits', 0)
        num_contributors = extract_contributors_from_commits(repo_data.get('commits', []))

        # Update statistics
        owner_stats[owner]['num_projects'] += 1
        owner_stats[owner]['total_contributors'] += num_contributors
        owner_stats[owner]['total_stars'] += stars
        owner_stats[owner]['age'] += calculate_project_age(repo.get('created_at'))

        language_stats[language]['num_projects'] += 1
        language_stats[language]['total_contributors'] += num_contributors
        language_stats[language]['total_stars'] += stars
        language_stats[language]['age'] += calculate_project_age(repo.get('created_at'))

        data.append({
            'Language': language,
            'Stars': stars,
            'Commits': total_commits,
            'Contributors': num_contributors,
            'Size': size,
            'Age': calculate_project_age(repo.get('created_at')),
        })

    # Convert to DataFrame
    df = pd.DataFrame(data)
    return df, language_stats, owner_stats


def calculate_summary_statistics(df):
    """Calculate summary statistics for each metric and return as a DataFrame."""
    summary_stats = {
        'Metric': ['Stars', 'Commits', 'Contributors', 'Size', 'Age'],
        'Count': [sum(df['Stars']), sum(df['Commits']), sum(df['Contributors']), sum(df['Size']), sum(df['Age'])],
        'Average': [
            round(df['Stars'].mean(), 2),
            round(df['Commits'].mean(), 2),
            round(df['Contributors'].mean(), 2),
            round(df['Size'].mean(), 2),
            round(df['Age'].mean(), 2)
        ],
        'Median': [
            round(df['Stars'].median(), 2),
            round(df['Commits'].median(), 2),
            round(df['Contributors'].median(), 2),
            round(df['Size'].median(), 2),
            round(df['Age'].median(), 2)
        ]
    }
    summary_df = pd.DataFrame(summary_stats)
    return summary_df


def compile_metric_statistics(stats_dict, column_name):
    """Compile and return statistics as a DataFrame."""
    data = []
    for metric, stats in stats_dict.items():
        num_projects = stats['num_projects']
        avg_contributors = stats['total_contributors'] / num_projects if num_projects > 0 else 0
        avg_stars = stats['total_stars'] / num_projects if num_projects > 0 else 0
        avg_age = stats['age'] / num_projects if num_projects > 0 else 0
        data.append({
            column_name: metric,
            'Number of Projects': num_projects,
            'Average Contributors': round(avg_contributors),
            'Average Stars': round(avg_stars),
            'Average Age in Years': round(avg_age, 1)
        })

    return pd.DataFrame(data)


def compile_overall_results(repositories, dataset, classification_matrix, correlations,
                            filename='overall_results.txt'):
    """
    Compiles overall important results into a single text file.
    """
    with open(RESULTS / filename, 'w') as file:
        # Gather repository data
        df, language_stats, owner_stats = gather_repo_data(dataset)

        # Calculate and display summary statistics
        summary_df = calculate_summary_statistics(df)
        file.write("Summary Statistics Table:\n")
        file.write(tabulate(summary_df, headers="keys", tablefmt="grid"))
        file.write("\n\n")

        # Compile and display language statistics
        language_df = compile_metric_statistics(language_stats, 'Language')
        file.write("Language Statistics Table:\n")
        file.write(tabulate(language_df, headers="keys", tablefmt="grid"))
        file.write("\n\n")

        # Compile and display owner statistics
        owner_df = compile_metric_statistics(owner_stats, 'Owner')
        file.write("Owner Statistics Table:\n")
        file.write(tabulate(owner_df, headers="keys", tablefmt="grid"))
        file.write("\n\n")

        # Overall Results
        total_repos = len(repositories)
        commit_count = sum([repo['analysis_summary']['total_commits'] for repo in repositories])
        cc_repos = [repo for repo in repositories if repo['analysis_summary']['cc_adoption_date'] is not None]
        consistent_repos = [repo for repo in repositories if repo['analysis_summary']['is_consistently_conventional']]
        cc_constantly_adopted = len(consistent_repos)
        cc_adoption_percentage = len(cc_repos) / total_repos * 100 if total_repos > 0 else 0

        file.write(f"Total Repositories: {total_repos}\n")
        file.write(f"Total Commits: {commit_count}\n")
        file.write("\n" + "-" * 50 + "\n")
        file.write(f"Average Commits per Repository: {commit_count / total_repos:.2f}\n")
        median_commits = np.median([repo['analysis_summary']['total_commits'] for repo in repositories])
        file.write(f"Median Commits per Repository: {median_commits:.2f}\n")
        file.write("\n" + "-" * 50 + "\n")
        avg_size = np.mean([repo['analysis_summary']['size'] for repo in repositories])
        median_size = np.median([repo['analysis_summary']['size'] for repo in repositories])
        file.write(f"Average Size per Repository: {avg_size:.2f}\n")
        file.write(f"Median Size per Repository: {median_size:.2f}\n")
        file.write("\n" + "-" * 50 + "\n")
        file.write(f"CC Repositories (consistently adopted): {cc_constantly_adopted}\n")
        file.write(f"CC Repositories: {len(cc_repos)}\n")
        file.write(f"CC Adoption Proportion: {cc_adoption_percentage:.2f}%\n")
        file.write(f"Non-CC Repositories: {total_repos - len(cc_repos)}\n")
        file.write("\n" + "-" * 50 + "\n")

        # Classification matrix
        file.write("\nTable: Comparison of CC Indication and CC Adoption\n")
        file.write(tabulate(classification_matrix, headers='keys', tablefmt='grid'))
        file.write("\n")

        # Correlations
        file.write("\nCorrelations between CC adoption and repository metrics:\n")
        for metric, value in correlations.items():
            file.write(f"Correlation between CC adoption and {metric}: {value:.2f}\n")

    print(f"Overall results saved to {filename}")
