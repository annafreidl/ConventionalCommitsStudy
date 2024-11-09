# Change in commits before and after the transition to conventional commits.

# – How does the average number of files changed per commit change after the adoption
# of conventional commits? Are commits more focused, with fewer files changed per
# commit, or do they become broader in scope?
#
# – Does the number of insertions and deletions per commit increase, decrease, or stay
# the same after the switch? This will help determine whether conventional com-
# mits encourage more granular changes, or simply a change in the way changes
# are grouped within commits.

# – Are there specific types of files (e.g. source code, configuration files, documenta-
# tion) that are more or less likely to be modified after the introduction of conventional
# commits? This might reveal changes in development practices or priorities.

# – Does the adoption of conventional commits lead to more frequent commits, or does
# # it simply change the way changes are structured within existing commit frequencies

from matplotlib import pyplot as plt
import os
import json
import pandas as pd
import seaborn as sns


# TODO:
# A: Gesamtanzahl der Commits in 2 Gruppen unterteilen: vor und nach Adoption von Conventional Commits
from constants import PLOTS


def load_and_filter_commits(repos):
    """
    Loads all commits from JSON files and filters out repositories without a cc_adoption_date.

    Parameters:
        results_dir (str or Path): Directory containing the JSON files of the repositories.

    Returns:
        pd.DataFrame: DataFrame with commits from repositories with a valid cc_adoption_date.
    """
    all_commits = []

    for repo in repos:
        summary = repo.get('analysis_summary', {})
        id = summary.get('id')
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
                'repository': id,
                'commit_date': commit_date,
                'files_changed': commit.get('files_changed', 0),
                'insertions': commit.get('insertions', 0),
                'deletions': commit.get('deletions', 0),
                'group': group
            })

    df = pd.DataFrame(all_commits)
    return df

# 2.1 Commit Analyse nach:
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


# - files changed per commit
# - insertions per commit
# - deletions per commit
# - Zeitraum zu vorherigem Commit

def plot_commit_ratios_detailed(avg_metrics):
    """
    Erstellt ein gestapeltes Balkendiagramm für CC-Commits vor und nach der Adoption.

    Parameters:
        avg_metrics (pd.DataFrame): DataFrame mit durchschnittlichen Kennzahlen.

    Returns:
        None
    """
    # Sicherstellen, dass die notwendigen Gruppen vorhanden sind
    required_groups = ['Vor', 'Nicht-CC', 'CC', 'Custom-CC']
    for group in required_groups:
        if group not in avg_metrics.index:
            avg_metrics.loc[group] = [0, 0, 0, 0]

    # Extrahieren der Werte für die Plot-Gruppen
    vor = avg_metrics.loc['Vor', 'total_commits']
    nicht_cc = avg_metrics.loc['Nicht-CC', 'total_commits']
    standard_cc = avg_metrics.loc['CC', 'total_commits']
    custom_cc = avg_metrics.loc['Custom-CC', 'total_commits']

    # Gruppen für das Plotten
    groups = ['Vor', 'Nach']

    # Werte für die gestapelten Balken
    vor_values = [vor]
    nach_values = [nicht_cc, standard_cc, custom_cc]

    # Farben für die einzelnen Kategorien
    colors = ['lightgrey', 'silver', 'skyblue', 'salmon']

    # Initialisierung der Plot-Figur
    plt.figure(figsize=(10, 6))
    sns.set(style="whitegrid")

    # Plot für 'Vor' Gruppe
    plt.bar(groups[0], vor_values[0], label='Vor Adoption', color=colors[0])

    # Plot für 'Nach' Gruppe mit gestapelten Kategorien
    bottom_nach = 0
    nach_labels = ['Nicht-CC Commits', 'Standard-CC Commits', 'Custom-CC Commits']
    for i, value in enumerate(nach_values):
        plt.bar(groups[1], value, bottom=bottom_nach, label=nach_labels[i], color=colors[i + 1])
        bottom_nach += value

    # Beschriftungen und Titel
    plt.xlabel('Commit-Gruppe')
    plt.ylabel('Anzahl der Commits')
    plt.title('Verhältnis von CC-Commits vor und nach der Adoption')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()

    # Speichern und Anzeigen des Plots
    plt.savefig('commit_ratios_detailed.png', dpi=300)
    plt.show()


def plot_average_metrics(avg_metrics):
    """
    Erstellt Balkendiagramme für die durchschnittlichen Kennzahlen.

    Parameters:
        avg_metrics (pd.DataFrame): DataFrame mit durchschnittlichen Kennzahlen.

    Returns:
        None
    """
    metrics = ['files_changed_avg', 'insertions_avg', 'deletions_avg']
    titles = ['Average Number of Files Changed per Commit',
              'Average Insertions per Commit',
              'Average Deletions per Commit']

    plt.figure(figsize=(18, 5))
    sns.set(style="whitegrid")

    for i, metric in enumerate(metrics):
        plt.subplot(1, 3, i + 1)
        sns.barplot(x=avg_metrics.index, y=avg_metrics[metric], palette='viridis')
        plt.title(titles[i])
        plt.xlabel('Commit-Gruppe')
        plt.ylabel('Durchschnittlicher Wert')
        plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig('average_metrics.png', dpi=300)
    plt.show()


def plot_cc_rates_scatter(df):
    """
    Erstellt einen Scatter Plot für die CC-Rate und Custom-CC-Rate.

    Parameters:
        df (pd.DataFrame): DataFrame mit den berechneten Raten.

    Returns:
        None
    """
    plt.figure(figsize=(10, 6))
    sns.set(style="whitegrid")

    scatter = sns.scatterplot(
        data=df,
        x='CC Rate',
        y='Custom CC Rate',
        size='total_commits',
        hue='CC Rate',
        palette='viridis',
        alpha=0.7,
        edgecolor='w',
        sizes=(20, 200),
        legend='brief'
    )

    plt.xlabel('CC Rate (Standard + Custom Commits / Total Commits)')
    plt.ylabel('Custom CC Rate (Custom CC Commits / CC Commits)')
    plt.title('Verhältnis von CC-Commits zu allen Commits und Custom-CC Commits zu CC Commits')
    plt.legend(title='CC Rate', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('cc_commit_rates_scatter_detailed.png', dpi=300)
    plt.show()


def plot_rate_distributions(df):
    """
    Erstellt Histogramme für die Verteilung der CC-Raten und Custom-CC-Raten.

    Parameters:
        df (pd.DataFrame): DataFrame mit den berechneten Raten.

    Returns:
        None
    """
    plt.figure(figsize=(14, 6))
    sns.set(style="whitegrid")

    # Histogramm für CC Rate
    plt.subplot(1, 2, 1)
    sns.histplot(df['CC Rate'], bins=30, kde=True, color='steelblue')
    plt.xlabel('CC Rate (Standard + Custom Commits / Total Commits)')
    plt.ylabel('Anzahl der Repositories')
    plt.title('Verteilung der CC-Raten über alle Repositories')

    # Histogramm für Custom CC Rate
    plt.subplot(1, 2, 2)
    sns.histplot(df['Custom CC Rate'], bins=30, kde=True, color='salmon')
    plt.xlabel('Custom CC Rate (Custom CC Commits / CC Commits)')
    plt.ylabel('Anzahl der Repositories')
    plt.title('Verteilung der Custom CC-Raten über alle Repositories')

    plt.tight_layout()
    plt.savefig('rate_distributions_detailed.png', dpi=300)
    plt.show()


# TODO
# B: Gesamtanzahl der Commits in 3 Gruppen unterteilen: CC-Commits, Custom-Type_Commits und nicht-CC-Commits

def load_and_group_commits_detailed(results_dir):
    """
    Lädt alle Commits aus den JSON-Dateien und gruppiert sie in CC, Custom-CC und Nicht-CC Commits.

    Parameters:
        results_dir (str or Path): Verzeichnis, das die JSON-Dateien der Repositories enthält.

    Returns:
        pd.DataFrame: DataFrame mit detaillierten Commit-Gruppen und berechneten Raten.
    """
    all_commits = []

    for filename in os.listdir(results_dir):
        if filename.endswith('.json'):
            filepath = Path(results_dir) / filename
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                summary = data.get('analysis_summary', {})
                adoption_date_str = summary.get('cc_adoption_date')

                # Überspringen von Repositories ohne Adoption Date
                if not adoption_date_str:
                    continue

                adoption_date = datetime.strptime(adoption_date_str, "%Y-%m-%d")
                commits = data.get('commits', [])

                for commit in commits:
                    commit_date = datetime.strptime(commit['committed_datetime'], "%Y-%m-%dT%H:%M:%S")
                    if commit_date >= adoption_date:
                        if commit['is_conventional']:
                            if commit['custom_type']:
                                group = 'Custom-CC'
                            else:
                                group = 'CC'
                        else:
                            group = 'Nicht-CC'
                    else:
                        group = 'Vor'

                    all_commits.append({
                        'repository': Path(filename).stem.replace('_commit_messages', ''),
                        'commit_date': commit_date,
                        'files_changed': commit.get('files_changed', 0),
                        'insertions': commit.get('insertions', 0),
                        'deletions': commit.get('deletions', 0),
                        'group': group
                    })

    df = pd.DataFrame(all_commits)
    return df


# 2.1 Commit Analyse nach:
def calculate_average_metrics_detailed(df):
    """
    Berechnet die durchschnittlichen Kennzahlen für detaillierte Commit-Gruppen.

    Parameters:
        df (pd.DataFrame): DataFrame mit detaillierten Commit-Gruppen.

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


# - files changed per commit
# - insertions per commit
# - deletions per commit
# - Zeitraum zu vorherigem Commit


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
    plt.rc('font', size=10)        # Standard-Schriftgröße
    plt.rc('axes', titlesize=10)   # Titel-Schriftgröße
    plt.rc('axes', labelsize=9)    # Achsenbeschriftungs-Schriftgröße
    plt.rc('xtick', labelsize=8)   # X-Achsen-Tick-Schriftgröße
    plt.rc('ytick', labelsize=8)   # Y-Achsen-Tick-Schriftgröße

    # Iteration über die Metriken und Erstellung der Subplots
    for i, metric in enumerate(metrics):
        # Erstellung eines Subplots für jede Metrik (3 Subplots nebeneinander)
        ax = plt.subplot(1, 3, i+1)

        sns.barplot(
            x=avg_metrics.index,
            y=avg_metrics[metric],
            palette='viridis',
            ax=ax
        )

        ax.set_title(titles[i], fontsize=10)   # Titel für jeden Subplot
        ax.set_xlabel('Commit-Gruppe', fontsize=9)  # X-Achsen-Beschriftung
        ax.set_ylabel(y_labels[i], fontsize=9)      # Y-Achsen-Beschriftung
        ax.tick_params(axis='x', rotation=45, labelsize=8)  # Drehen der X-Achsen-Beschriftungen
        ax.tick_params(axis='y', labelsize=8)               # Y-Achsen-Beschriftungsgröße

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
    plt.savefig(PLOTS/'average_metrics_detailed.pdf', bbox_inches='tight')  # Speichern der Figur als PDF
    plt.show()  # Anzeige des Plots



# 2.2 Files changed per commit nach Dateityp --> evtl. Exkurs


from datetime import datetime
from pathlib import Path
from RQ1 import set_logging

COUNTER_LEVEL = 25
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
RESULTS = ROOT / r"results" / r"commit_messages"
YAML = ROOT / "data" / "dataset.yaml"

if __name__ == "__main__":
    logger = set_logging()

    RESULTS.mkdir(exist_ok=True)

    # Laden der Commits und Gruppierung vor/nach CC-Adoption
    results_directory = RESULTS  # Pfad zu Ihrem RESULTS-Verzeichnis
    df_before_after = load_and_filter_commits(results_directory)

    # Berechnung der durchschnittlichen Kennzahlen
    avg_metrics_before_after = calculate_average_metrics(df_before_after)
    avg_metrics_before_after = avg_metrics_before_after.loc[::-1]

    # Anzeigen der Ergebnisse
    print(avg_metrics_before_after)

    # Laden der detaillierten Commit-Gruppen
    df_detailed = load_and_group_commits_detailed(results_directory)

    # Überprüfen der Spalten im DataFrame
    print("Spalten im DataFrame:", df_detailed.columns.tolist())

    # Anzeigen der ersten Zeilen des DataFrames
    print(df_detailed.head())

    # Berechnung der durchschnittlichen Kennzahlen
    avg_metrics_detailed = calculate_average_metrics_detailed(df_detailed)

    # Anzeigen der Ergebnisse
    print(avg_metrics_detailed)

    # Plot 1: Verhältnis von CC-Commits zu allen Commits (gestapeltes Balkendiagramm)
    plot_commit_ratios_detailed(avg_metrics_detailed)

    # Plot 2: Veränderung der durchschnittlichen Kennzahlen
    plot_average_metrics_detailed(avg_metrics_before_after)

    # Plot 4: Verteilung der CC-Raten und Custom-CC-Raten (Histogramme)
    plot_rate_distributions(df_detailed)
