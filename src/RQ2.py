from datetime import datetime
from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns

from constants import PLOTS


def analyze_commit_length(commits_after, commits_before):
    message_length_before = [len(commit.get('message')) for commit in commits_before]
    message_length_after = [len(commit.get('message')) for commit in commits_after]

    print(
        f"Durchschnittliche Commit-Nachrichtenlänge vor CC-Adoption: "
        f"{sum(message_length_before) / len(message_length_before):.2f} Zeichen")
    print(
        f"Durchschnittliche Commit-Nachrichtenlänge nach CC-Adoption: "
        f"{sum(message_length_after) / len(message_length_after):.2f} Zeichen")


def analyze_rq2(repos):
    """
    Performs analysis related to Research Question 2.
    """
    # Load and filter commits before and after CC adoption
    df = load_and_filter_commits(repos)

    after_commits = df[df['group'] == 'after'].to_dict(orient='records')
    before_commits = df[df['group'] == 'before'].to_dict(orient='records')

    analyze_commit_frequency(after_commits, before_commits)
    analyze_commit_length(after_commits, before_commits)

    # Calculate average metrics before and after CC adoption
    avg_metrics_before_after = calculate_average_metrics(df)
    avg_metrics_before_after = avg_metrics_before_after.loc[::-1]
    print(avg_metrics_before_after)

    # Plot average metrics detailed before and after CC adoption
    plot_average_metrics_detailed(avg_metrics_before_after)


def analyze_commit_frequency(commits_before, commits_after):
    """
    Analysiert die Commit-Frequenz vor und nach der CC-Adoption.

    Parameters:
    - commits_before (list of dict): Commits vor der CC-Adoption.
    - commits_after (list of dict): Commits nach der CC-Adoption.
    """

    # Berechnung der Dauer in Tagen
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

    print(f"Commit-Frequenz vor CC-Adoption: {frequency_before:.2f} Commits/Tag")
    print(f"Commit-Frequenz nach CC-Adoption: {frequency_after:.2f} Commits/Tag")


def calculate_average_metrics(df):
    """
    Berechnet die durchschnittlichen Kennzahlen vor und nach der CC-Adoption.

    Parameters:
        df (pd.DataFrame): DataFrame mit gruppierten Commit-Daten.

    Returns:
        pd.DataFrame: DataFrame mit den durchschnittlichen Kennzahlen.
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


def load_and_filter_commits(repos):
    """
    Loads all commits from JSON files and filters out repositories without a cc_adoption_date.

    Parameters:
        :param repos:

    Returns:
        pd.DataFrame: DataFrame with commits from repositories with a valid cc_adoption_date.

    """
    all_commits = []

    for repo in repos:
        summary = repo.get('analysis_summary', {})
        identity = summary.get('id')
        adoption_date_str = summary.get('cc_adoption_date')

        # Skip repositories without an adoption date
        if not adoption_date_str:
            continue

        adoption_date = datetime.strptime(adoption_date_str, "%Y-%m-%d")
        commits = repo.get('commits', [])

        for commit in commits:
            commit_date = datetime.strptime(commit['committed_datetime'], "%Y-%m-%dT%H:%M:%S")
            group = 'after' if commit_date >= adoption_date else 'before'

            all_commits.append({
                'repository': identity,
                'commit_date': commit_date,
                'message': commit.get('message', ''),
                'files_changed': commit.get('files_changed', 0),
                'insertions': commit.get('insertions', 0),
                'deletions': commit.get('deletions', 0),
                'group': group
            })

    df = pd.DataFrame(all_commits)
    return df


def plot_average_metrics_detailed(avg_metrics):
    """
    Erstellt Balkendiagramme für die durchschnittlichen Metriken vor und nach der CC-Adoption.

    Parameter:
        avg_metrics (pd.DataFrame): DataFrame mit den gruppierten Commit-Daten.

    Rückgabewert:
        None
    """
    metrics = ['files_changed_avg', 'insertions_avg', 'deletions_avg']
    titles = [
        'Average number of changed files per commit',
        'Average insertions per commit',
        'Average deletions per commit'
    ]
    y_labels = ['Avg. changed files', 'Avg. insertions', 'Avg. deletions']

    # Festlegen der Figurengröße für drei nebeneinander liegende Plots
    plt.figure(figsize=(12, 4))  # Breite von 12 Zoll, Höhe von 4 Zoll

    # Anpassen der Schriftarten für bessere Lesbarkeit
    plt.rc('font', size=10)  # Standard-Schriftgröße
    plt.rc('axes', titlesize=10)  # Titel-Schriftgröße
    plt.rc('axes', labelsize=9)  # Achsenbeschriftungs-Schriftgröße
    plt.rc('xtick', labelsize=8)  # X-Achsen-Tick-Schriftgröße
    plt.rc('ytick', labelsize=8)  # Y-Achsen-Tick-Schriftgröße

    # Iteration über die Metriken und Erstellung der Subplots
    for i, metric in enumerate(metrics):
        # Erstellung eines Subplots für jede Metrik (3 Subplots nebeneinander)
        ax = plt.subplot(1, 3, i + 1)

        sns.barplot(
            x=avg_metrics.index,
            y=avg_metrics[metric],
            palette='viridis',
            ax=ax
        )

        ax.set_title(titles[i], fontsize=10)  # Titel für jeden Subplot
        ax.set_xlabel('Commit-Gruppe', fontsize=9)  # X-Achsen-Beschriftung
        ax.set_ylabel(y_labels[i], fontsize=9)  # Y-Achsen-Beschriftung
        ax.tick_params(axis='x', rotation=45, labelsize=8)  # Drehen der X-Achsen-Beschriftungen
        ax.tick_params(axis='y', labelsize=8)  # Y-Achsen-Beschriftungsgröße

        # Optional: Anzeige der genauen Werte über den Balken
        for p in ax.patches:
            height = p.get_height()
            ax.annotate(
                f'{height:.2f}',
                (p.get_x() + p.get_width() / 2., height + 0.5),
                ha='center', va='bottom',
                fontsize=8
            )

    plt.tight_layout()  # Anpassung des Layouts, um Überlappungen zu vermeiden
    plt.savefig(PLOTS / 'average_metrics_detailed.pdf', bbox_inches='tight')  # Speichern der Figur als PDF
    plt.show()  # Anzeige des Plots
