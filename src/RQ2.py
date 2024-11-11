from datetime import datetime
from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
from constants import PLOTS

colors = ['#e6f4e6', '#c3e6c3', '#a1d8a1', '#7eca7e', '#5cbd5c', '#4da64d', '#3d8c3d']

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


def plot_ccp_before_after(df, df_consistent, df_adoption_date):

    adoption_after_commits = df_adoption_date[df_adoption_date['group'] == 'after'].to_dict(orient='records')
    adoption_before_commits = df_adoption_date[df_adoption_date['group'] == 'before'].to_dict(orient='records')

    cc_rate_before = sum(1 for commit in adoption_before_commits if commit.get('cc_commit')) / len(
        adoption_before_commits)
    cc_rate_after = sum(1 for commit in adoption_after_commits if commit.get('cc_commit')) / len(
        adoption_after_commits)
    consistent_rate = sum(1 for commit in df_consistent.to_dict(orient='records') if commit.get('cc_commit')) / len(
        df_consistent)

    data = pd.DataFrame({
        'Category': ['Consistent from start', 'Adopted Later (Before)', 'Adopted Later (After)'],
        'CCP': [round(consistent_rate * 100, 2), round(cc_rate_before * 100, 2), round(cc_rate_after * 100, 2)]
    })

    # Erstellen des Barplots
    plt.figure(figsize=(6.202, 4.652))
    ax = sns.barplot(x='Category', y='CCP', data=data, color=colors[6])
    ax.bar_label(ax.containers[0], fontsize=10)

    # Achsen und Titel
    plt.xlabel('Repository Category')
    plt.ylabel('Average CCP (%)')
    plt.ylim(0, 100)  # Annahme, dass der CCP zwischen 0 und 100 liegt
    # Anzeige des Plots

    plt.tight_layout()
    plt.savefig(PLOTS / 'CCP_before_after.pdf')
    plt.close()


def analyze_rq2(repos):
    """
    Performs analysis related to Research Question 2.
    """

    # Load and filter CC-commits before and after without consistent adoption
    df, df_consistent, df_adoption_date = load_and_filter_commits_adopted(repos)

    # Plot CCP before and after
    plot_ccp_before_after(df, df_consistent, df_adoption_date)

    # Calculate average metrics before and after CC adoption
    avg_metrics_before_after = calculate_average_metrics(df)
    avg_metrics_before_after = avg_metrics_before_after.loc[::-1]
    print(avg_metrics_before_after)

    # Plot average metrics detailed before and after CC adoption
    plot_average_metrics_detailed(avg_metrics_before_after)


def analyze_commit_length(commits_after, commits_before):
    message_length_before = [len(commit.get('message')) for commit in commits_before]
    message_length_after = [len(commit.get('message')) for commit in commits_after]

    print(
        f"Average commit message length before CC adoption: "
        f"{sum(message_length_before) / len(message_length_before):.2f} characters")
    print(
        f"Average commit message length after CC adoption: "
        f"{sum(message_length_after) / len(message_length_after):.2f} characters")


def analyze_cc_proportion(commits_after, commits_before):
    cc_rate_before = sum(1 for commit in commits_before if commit.get('cc_commit')) / len(commits_before)
    cc_rate_after = sum(1 for commit in commits_after if commit.get('cc_commit')) / len(commits_after)

    print(f"CC rate before CC adoption: {cc_rate_before:.2%}")
    print(f"CC rate after CC adoption: {cc_rate_after:.2%}")


def analyze_commit_frequency(commits_before, commits_after):
    """
    Analyzes commit frequency before and after CC adoption.

    Parameters:
    - commits_before (list of dict): Commits before CC adoption.
    - commits_after (list of dict): Commits after CC adoption.
    """

    # Calculate duration in days
    if commits_before:
        start_date_before = commits_before[-1].get('commit_date')
        end_date_before = commits_before[0].get('commit_date')
        days_before = (end_date_before - start_date_before).days or 1
        frequency_before = len(commits_before) / days_before
    else:
        frequency_before = 0

    if commits_after:
        start_date_after = commits_after[-1].get('commit_date')
        end_date_after = commits_after[0].get('commit_date')
        days_after = (end_date_after - start_date_after).days or 1
        frequency_after = len(commits_after) / days_after
    else:
        frequency_after = 0

    print(f"Commit frequency before CC adoption: {frequency_before:.2f} commits/day")
    print(f"Commit frequency after CC adoption: {frequency_after:.2f} commits/day")


def calculate_average_metrics(df):
    """
    Calculates average metrics before and after CC adoption.

    Parameters:
        df (pd.DataFrame): DataFrame with grouped commit data.

    Returns:
        pd.DataFrame: DataFrame with average metrics.
    """
    avg_metrics = df.groupby('group').agg({
        'files_changed': 'mean',
        'insertions': 'mean',
        'deletions': 'mean',
        'commit_date': 'count'
    }).rename(columns={'commit_date': 'total_commits'})

    avg_metrics['files_changed_avg'] = avg_metrics['files_changed'].round(2)
    avg_metrics['insertions_avg'] = avg_metrics['insertions'].round(2)
    avg_metrics['deletions_avg'] = avg_metrics['deletions'].round(2)

    return avg_metrics[['files_changed_avg', 'insertions_avg', 'deletions_avg', 'total_commits']]


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

    total_cc_commits_rate = commits_cc / len_commits * 100
    total_custom_commits_rate = commits_custom / len_commits * 100
    cc_commits_rate = cc_commits_cc / len_cc_commits * 100
    custom_commits_rate = cc_commits_custom / len_cc_commits * 100

    return total_cc_commits_rate, total_custom_commits_rate, cc_commits_rate, custom_commits_rate


def load_and_filter_commits_adopted(repos):
    """
    Loads all commits from JSON files and filters out repositories without a cc_adoption_date.

    Parameters:
        repos (list of dict): List of repository data.

    Returns:
        pd.DataFrame: DataFrame with commits from repositories with a valid cc_adoption_date.
    """
    all_commits = []
    all_commits_consistent = []
    all_commits_adoption_date = []

    for repo in repos:
        summary = repo.get('analysis_summary', {})
        identity = summary.get('id')
        adoption_date_str = summary.get('cc_adoption_date')

        # Skip repositories without an adoption date
        if not adoption_date_str:
            continue

        adoption_date = datetime.strptime(adoption_date_str, "%Y-%m-%d")
        commits = repo.get('commits', [])
        consistently_cc = summary.get('is_consistently_conventional')

        for commit in commits:
            commit_date = datetime.strptime(commit['committed_datetime'], "%Y-%m-%dT%H:%M:%S")
            group = 'after' if commit_date >= adoption_date else 'before'

            commit_filled = {
                'repository': identity,
                'commit_date': commit_date,
                'message': commit.get('message', ''),
                'files_changed': commit.get('files_changed', 0),
                'insertions': commit.get('insertions', 0),
                'deletions': commit.get('deletions', 0),
                'cc_commit': commit.get('cc_type', None),
                'group': group,
                'consistent': consistently_cc
            }

            if consistently_cc:
                all_commits_consistent.append(commit_filled)
            else:
                all_commits_adoption_date.append(commit_filled)

            all_commits.append(commit_filled)

    df = pd.DataFrame(all_commits)
    df_consistent = pd.DataFrame(all_commits_consistent)
    df_adoption_date = pd.DataFrame(all_commits_adoption_date)
    return df, df_consistent, df_adoption_date


def plot_average_metrics_detailed(avg_metrics):
    """
    Creates bar plots for average metrics before and after CC adoption.

    Parameters:
        avg_metrics (pd.DataFrame): DataFrame with grouped commit data.

    Returns:
        None
    """
    metrics = ['files_changed_avg', 'insertions_avg', 'deletions_avg']
    titles = [
        'Average number of changed files per commit',
        'Average insertions per commit',
        'Average deletions per commit'
    ]
    y_labels = ['Avg. changed files', 'Avg. insertions', 'Avg. deletions']

    # Set figure size for three side-by-side plots
    plt.figure(figsize=(12, 4))  # Width 12 inches, height 4 inches

    # Adjust font settings for better readability
    plt.rc('font', size=10)  # Standard font size
    plt.rc('axes', titlesize=10)  # Title font size
    plt.rc('axes', labelsize=9)  # Axis label font size
    plt.rc('xtick', labelsize=8)  # X-axis tick label font size
    plt.rc('ytick', labelsize=8)  # Y-axis tick label font size

    # Iterate over metrics and create subplots
    for i, metric in enumerate(metrics):
        # Create a subplot for each metric (3 side-by-side subplots)
        ax = plt.subplot(1, 3, i + 1)

        sns.barplot(
            x=avg_metrics.index,
            y=avg_metrics[metric],
            palette='viridis',
            ax=ax
        )

        ax.set_title(titles[i], fontsize=10)  # Title for each subplot
        ax.set_xlabel('Commit Group', fontsize=9)  # X-axis label
        ax.set_ylabel(y_labels[i], fontsize=9)  # Y-axis label
        ax.tick_params(axis='x', rotation=45, labelsize=8)  # Rotate X-axis labels
        ax.tick_params(axis='y', labelsize=8)  # Y-axis label size

        # Optionally display exact values above bars
        for p in ax.patches:
            height = p.get_height()
            ax.annotate(
                f'{height:.2f}',
                (p.get_x() + p.get_width() / 2., height + 0.5),
                ha='center', va='bottom',
                fontsize=8
            )

    plt.tight_layout()  # Adjust layout to avoid overlap
    plt.savefig(PLOTS / 'average_metrics_detailed.pdf', bbox_inches='tight')  # Save figure as PDF
    plt.show()  # Display plot
