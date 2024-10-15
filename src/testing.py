from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import ruptures as rpt
import seaborn as sns
from dateutil.relativedelta import relativedelta
from matplotlib.lines import Line2D

from constants import CHUNK_SIZE_PERCENT, NUM_CHUNKS, MIN_CC_PERCENTAGE
from data_saver import load_from_json, load_dataset
from repository_manager import clone_repository


def chunk_data(commits, chunk_size):
    """
    Teilt die Commit-Liste in Chunks auf.

    Args:
        commits (list): Liste der Commits.
        chunk_size (int): Größe jedes Chunks.

    Yields:
        list: Ein Chunk von Commits.
    """
    total_commits = len(commits)
    for i in range(0, total_commits, chunk_size):
        yield commits[i:i + chunk_size]


def analyse_commit_chunks(commit_data, repository_name):
    """
    Analysiert die Commits eines Repositories und bestimmt, ob eine konsequente CC-Nutzung vorliegt.

    Args:
        commit_data (dict): Daten des Repositories mit Commits und Analyseergebnissen.
        repository_name (str): Name des Repositories.

    Returns:
        bool: True, wenn eine konsequente CC-Nutzung erkannt wurde, sonst False.
    """
    print(repository_name)
    commits = commit_data.get("commits", [])
    analysis_summary = commit_data.get("analysis_summary", {})

    cc_type_commits = analysis_summary.get("cc_type_commits", 0)
    total_commits = analysis_summary.get("total_commits", 0)

    if total_commits == 0:
        print("Keine Commits für die Analyse verfügbar.")
        return False

    # Berechnung der Mindestgrenzen
    min_threshold_rel = cc_type_commits / total_commits
    min_threshold_abs = cc_type_commits > 200

    print(f"Mindestgrenze (relativ): {min_threshold_rel}")
    print(f"Mindestgrenze erfüllt (relativ): {min_threshold_rel >= 0.05}")
    print(f"Mindestgrenze erfüllt (absolut): {min_threshold_abs}")
    print(f"Anzahl CC-Commits: {cc_type_commits}")

    if min_threshold_rel >= 0.05 and min_threshold_abs:
        print("Beide Mindestgrenzen sind erfüllt.")

        # Berechnung der Chunk-Größe
        chunk_size = total_commits // NUM_CHUNKS
        print(f"Chunk-Größe: {chunk_size}")

        chunk_cc_rates = []

        for chunk in chunk_data(commits, chunk_size):
            cc_commit_count = sum(1 for commit in chunk if commit.get("cc_type") is not None)
            chunk_cc_rate = cc_commit_count / len(chunk)
            chunk_cc_rates.append(round(chunk_cc_rate, 2))

        reversed_chunk_rates = chunk_cc_rates[::-1]
        cc_adoption_chunk_index = find_cc_chunk_adoption_date(reversed_chunk_rates)

        if cc_adoption_chunk_index != -1:
            adoption_commit_index = ((NUM_CHUNKS - cc_adoption_chunk_index) * chunk_size) - 1
            adoption_date = commits[adoption_commit_index].get("committed_datetime")
            previous_adoption_date = analysis_summary.get('cc_adoption_date')

            print(f"Erstes CC-Commit Datum: {adoption_date}")
            print(f"Vorheriges Adoption-Datum: {previous_adoption_date}")

            if previous_adoption_date:
                date_old = datetime.fromisoformat(previous_adoption_date)
                date_new = datetime.fromisoformat(adoption_date)
                diff = relativedelta(date_new, date_old)
                months_diff = diff.years * 12 + diff.months
                print(f"Unterschied in Monaten: {months_diff}")

            print(f"Konsequente CC-Nutzung ab Chunk {cc_adoption_chunk_index}")
            visualize_commit_chunks(reversed_chunk_rates, chunk_size)
            if previous_adoption_date:
                print("Unverändertes Ergebnis")
            else:
                print("Neue CC-Nutzung erkannt")
            return True
        else:
            if analysis_summary.get("cc_adoption_date"):
                print("CC-Nutzung nicht mehr erkannt")
            else:
                print("Unverändertes Ergebnis")
            print("Keine konsequente CC-Nutzung")
            return False
    else:
        print("Zu wenige Commits für eine Analyse.")
        return False


def visualize_commit_chunks(chunkliste, ganze_chunks):
    percent = [wert * 100 for wert in chunkliste]

    # Erstelle die x-Achsen-Beschriftungen (1, 2, 3, ...)
    x_achsen = list(range(0, len(percent)))

    # Erstelle das Balkendiagramm
    plt.figure(figsize=(10, 6))
    bars = plt.bar(x_achsen, percent, color='skyblue')

    # Setze die y-Achse von 0% bis 100%
    plt.ylim(0, 100)

    # Beschrifte die Achsen
    plt.title(f'Chunksize = {ganze_chunks}')
    plt.xlabel('Datenpunkt')
    plt.ylabel('Prozent (%)')

    # Setze die x-Achsen-Ticks auf die Datenpunkte
    plt.xticks(x_achsen)

    # Füge Prozentwerte über den Balken hinzu
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, height, f'{height}%', ha='center', va='bottom')

    # Zeige das Diagramm
    plt.tight_layout()
    plt.show()


def count_chunks(chunklist):
    # Anzahl der CC-Chunks in der Liste
    return sum(1 for x in chunklist if x >= MIN_CC_PERCENTAGE)


def find_cc_chunk_adoption_date(chunk_rates):
    """
    Findet den Index des Chunks, ab dem die CC-Nutzung konsequent ist.

    Args:
        chunk_rates (list): Liste der CC-Raten pro Chunk (umgekehrt sortiert).

    Returns:
        int: Index des Chunks ab dem die CC-Nutzung konsequent ist, sonst -1.
    """
    for idx, rate in enumerate(chunk_rates):
        if rate >= MIN_CC_PERCENTAGE:
            return len(chunk_rates) - idx - 1  # Umrechnung auf Originalindex
    print("Keine konsequente CC-Nutzung gefunden.")
    return -1


def calculate_cusum(data):
    target_mean = np.mean(data)
    deviations = data - target_mean
    cusum_values = np.cumsum(deviations)
    return cusum_values


def plot_cusum(values):
    """
    Visualisiert die CUSUM-Kurve der CC-Nutzung.

    Args:
        values (numpy.array): Array der CUSUM-Werte.
    """
    plt.figure(figsize=(12, 6))
    plt.plot(values, marker='o')
    plt.title('CUSUM-Kurve der CC-Nutzung')
    plt.xlabel('Commit-Index')
    plt.ylabel('Kumulative Abweichung')
    plt.grid(True)
    plt.show()


def plot_heatmap(sequence):
    # 1. Daten vorbereiten
    heatmap_data = np.array(sequence).reshape(-1, 1)

    plt.figure(figsize=(12, 6))
    sns.heatmap(heatmap_data.T, cmap='YlGnBu', cbar=False)
    plt.title('Heatmap der CC-Nutzung über Commits')

    plt.axvline(x=change_point_index, color='red', linestyle='--', label='Change Point')

    # 5. Beschriftung des Change Points mit Hintergrund
    plt.annotate(f'Change Point\n{adoption_date}',
                 xy=(change_point_index, 0),
                 xytext=(change_point_index + len(sequence) * 0.05, 0.2),
                 arrowprops=dict(facecolor='red', shrink=0.05),
                 fontsize=10, color='black',
                 bbox=dict(boxstyle='round,pad=0.5', fc='yellow', ec='black', lw=1))

    plt.xlabel('Commit-Index')
    plt.ylabel('CC-Nutzung')
    plt.yticks([])
    plt.show()


if __name__ == "__main__":

    FILE = Path(__file__).resolve()
    ROOT = FILE.parents[0]
    RESULTS = ROOT / "results" / "commit_messages"
    YAML = ROOT / "data" / "test1.yaml"

    RESULTS.mkdir(exist_ok=True)
    repos = load_dataset(YAML)

    print(f"Anzahl Repos: {len(repos)}")

    cc_anwendungen = 0

    for repo_data in repos:
        repo_name = repo_data["name"].replace("/", "_")
        json_file_path = RESULTS / f"{repo_name}_commit_messages.json"

        repo = clone_repository(repo_data)
        print("Klonen abgeschlossen")

        data = load_from_json(json_file_path)
        print("Daten geladen")

        if data.get("analysis_summary", {}).get("total_commits", 0) > 0:
            cc_anwendung = analyse_commit_chunks(data, repo_data["name"])
            if cc_anwendung:
                cc_anwendungen += 1

                commits = data.get("commits", {})
                commits_reversed = commits[::-1]
                # Angenommen, 'commits' ist deine Liste von Commit-Daten
                commit_sequence = [1 if commit.get("cc_type") else 0 for commit in commits_reversed]

                # Berechnung der CUSUM-Statistik
                cusum_values = calculate_cusum(np.array(commit_sequence))
                print(f"CUSUM-Werte: {cusum_values}")

                signal = np.array(commit_sequence)
                model = "l2"
                algo = rpt.Binseg(model=model).fit(signal)
                change_points = algo.predict(n_bkps=1)  # 'n_bkps' ist die Anzahl der Change Points, die du erwartest

                print(f"Gefundene Change Points: {change_points}")

                # 5. Bestimme den Change Point Index
                if len(change_points) > 1:
                    change_point_index = change_points[0]
                    change_point_commit = commits_reversed[change_point_index]
                    adoption_date = change_point_commit.get('committed_datetime')[:10]
                    print(f"CC-Nutzung wurde ab dem {adoption_date} konsequent.")
                else:
                    print("Kein signifikanter Change Point gefunden.")

                # Visualisierung
                plot_heatmap(commit_sequence)

                # Visualisierung
                plot_cusum(cusum_values)

            print("Analyse abgeschlossen\n")
        else:
            print("Keine Commits vorhanden\n")

    print(f"Anzahl CC-Anwendungen: {cc_anwendungen}")
