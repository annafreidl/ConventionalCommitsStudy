import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import List, Optional, Dict

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

from constants import ROOT
from data_saver import load_classifications


def visualize_repo_commits(enriched_commits, summary, repo_name):
    """
    Visualisiert Commit-Daten eines Repositories basierend auf den angereicherten Commits und der Zusammenfassung.
    """
    custom_type_distribution = summary.get('custom_type_distribution', {})
    cc_type_distribution = summary.get('cc_type_distribution', {})

    # Visualisierungsfunktionen aufrufen
    visualize_cc_ratio(summary, repo_name)
    visualize_type_distribution(custom_type_distribution, f'Custom Types in {repo_name}', 'Custom Types')
    visualize_type_distribution(cc_type_distribution, f'CC Types in {repo_name}', 'CC Types')


def visualize_pie_chart(conventional_count, unconventional_count, project_name):
    """
    Visualisiert ein Kreisdiagramm basierend auf den konventionellen und nicht-konventionellen Commits.
    """

    labels = ['CC-Specification', 'Not CC-Specification']
    sizes = [conventional_count, unconventional_count]
    colors = ['#90ee90', '#f08080']

    def make_pct(values):
        total = sum(values)
        return lambda pct: f'{pct:.1f}%\n({int(round(pct * total / 100))})'

    plt.pie(sizes, labels=labels, colors=colors, autopct=make_pct(sizes), startangle=140)
    plt.title(f'Number of CC in project: {project_name}')
    plt.axis('equal')
    plt.show()


def visualize_cc_ratio(analysis_summary, project_name):
    """
    Erstellt ein Kreisdiagramm, das das Verhältnis von konventionellen zu nicht-konventionellen Commits visualisiert.
    """
    conventional_count = analysis_summary.get('conventional_commits', 0)
    unconventional_count = analysis_summary.get('unconventional_commits', 0)

    # Überprüfe, ob es überhaupt Commits gibt
    total_commits = conventional_count + unconventional_count
    if total_commits == 0:
        print(f"Keine Commits zum Analysieren für das Projekt {project_name}.")
        return

    # Kreisdiagramm visualisieren
    visualize_pie_chart(conventional_count, unconventional_count, project_name)


def visualize_type_distribution(type_distribution, title, x_label, top_n=20):
    """
    Visualisiert die Verteilung der Typen als Balkendiagramm, begrenzt auf die Top N häufigsten Typen.

    Args:
        type_distribution (dict): Dictionary mit Typen als Schlüssel und deren Häufigkeit als Wert.
        title (str): Titel des Diagramms.
        x_label (str): Bezeichnung der x-Achse.
        top_n (int): Anzahl der Top-Typen, die angezeigt werden sollen.
    """
    if not type_distribution:
        print(f"Keine Daten für {title} vorhanden.")
        return

    # Sortiere das Dictionary nach Häufigkeit absteigend und wähle die Top N aus
    sorted_types = sorted(type_distribution.items(), key=lambda item: item[1], reverse=True)[:top_n]
    types, counts = zip(*sorted_types)

    # Balkendiagramm erstellen
    plt.figure(figsize=(10, 6))
    plt.bar(types, counts, color='#87CEEB')
    plt.xlabel(x_label)
    plt.ylabel('Häufigkeit')
    plt.title(f'{title} (Top {top_n})')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()


def visualize_monthly_conventional_commits(cc_type_data, custom_type_data):
    """
    Visualisiert den prozentualen Anteil konventioneller Commits mit cc_type und custom_type pro Monat.

    Args:
        cc_type_data (dict): Dictionary mit dem Jahr-Monat als Schlüssel und dem prozentualen Anteil konventioneller Commits mit cc_type.
        custom_type_data (dict): Dictionary mit dem Jahr-Monat als Schlüssel und dem prozentualen Anteil konventioneller Commits mit custom_type.
    """
    # Sortiere die Monate chronologisch
    months = sorted(cc_type_data.keys())
    cc_type_percentages = [cc_type_data[month] for month in months]
    custom_type_percentages = [custom_type_data[month] for month in months]

    # Erstelle ein Liniendiagramm für beide Datensätze
    plt.figure(figsize=(12, 6))  # Größeres Diagramm für bessere Lesbarkeit
    plt.plot(months, cc_type_percentages, marker='o', linestyle='-', color='b', label='CC-Type')
    plt.plot(months, custom_type_percentages, marker='s', linestyle='--', color='r', label='Custom-Type')

    # Diagrammbeschriftungen
    plt.title('Prozentualer Anteil konventioneller Commits pro Monat (CC-Type vs. Custom-Type)')
    plt.xlabel('Monat')
    plt.ylabel('Anteil konventioneller Commits (%)')

    # X-Ticks reduzieren (z. B. nur jeden 6. Monat anzeigen) und Schriftgröße anpassen
    plt.xticks(ticks=range(0, len(months), 6), labels=[months[i] for i in range(0, len(months), 6)], rotation=45,
               ha='right', fontsize=10)

    # Gitterlinien und Layout anpassen
    plt.grid(True)
    plt.legend(loc='best')  # Legende für beide Linien
    plt.tight_layout()

    # Plot anzeigen
    plt.show()


def plot_cc_adoption_dates(results_dir):
    """
    Iteriert über alle JSON-Dateien im angegebenen Verzeichnis,
    prüft, ob 'cc_adoption_date' gesetzt ist und erstellt ein Kreisdiagramm.

    Args:
        results_dir (Path): Pfad zum Verzeichnis mit den JSON-Dateien.

    Returns:
        None
    """
    total_files = 0
    non_null_cc_adoption = 0

    # Iteriere über alle JSON-Dateien im Verzeichnis
    for json_file in results_dir.glob('*.json'):
        total_files += 1
        print(total_files)
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Zugriff auf 'cc_adoption_date' innerhalb von 'analysis_summary'
            cc_adoption_date = data.get('analysis_summary', {}).get('cc_adoption_date', None)
            if cc_adoption_date is not None:
                non_null_cc_adoption += 1
                print("CC-Adoption in", non_null_cc_adoption)
                print("Projektname: ", Path(json_file).name.split('.')[0])  # Gibt den Namen ohne Dateierweiterung aus

        except json.JSONDecodeError:
            print(f"Fehler beim Dekodieren der JSON-Datei: {json_file}")
        except Exception as e:
            print(f"Fehler beim Lesen der Datei {json_file}: {e}")

    # Berechne die Anzahl der Dateien ohne gesetztes 'cc_adoption_date'
    null_cc_adoption = total_files - non_null_cc_adoption

    # Daten für das Kreisdiagramm
    labels = ['cc_adoption_date gesetzt', 'cc_adoption_date null']
    sizes = [non_null_cc_adoption, null_cc_adoption]
    colors = ['green', 'red']  # Farben für die Segmente

    # Erstelle das Kreisdiagramm
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
    ax.axis('equal')  # Gleiches Seitenverhältnis, um den Kreis zu wahren
    plt.title('Verteilung der cc_adoption_date in den JSON-Dateien')
    plt.show()


def plot_classification_by_language(classification_file, output_dir):
    """
    Liest den Klassifikationsindex ein, sammelt die Daten und erstellt für jede Programmiersprache ein Diagramm der Repository-Klassifikationen.

    Args:
        classification_file (Path): Pfad zur JSON-Datei mit den Klassifikationen.
        output_dir (Path): Verzeichnis, in dem die Diagramme gespeichert werden sollen.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Lade die Klassifikationen
    with open(classification_file, 'r', encoding='utf-8') as f:
        classifications = json.load(f)

    for language, repos in classifications.items():
        # Zähle die Anzahl der Repositories pro Klassifikation für die aktuelle Sprache
        classification_counts = defaultdict(int)
        for classification in repos.values():
            classification_counts[classification] += 1

        # Sortiere die Klassifikationen nach Anzahl absteigend
        classifications_sorted = dict(sorted(classification_counts.items(), key=lambda item: item[1], reverse=True))

        classifications_list = list(classifications_sorted.keys())
        counts = list(classifications_sorted.values())

        plt.figure(figsize=(8, 6))
        bars = plt.bar(classifications_list, counts, color='#87CEEB')
        plt.xlabel('Klassifikation')
        plt.ylabel('Anzahl der Repositories')
        plt.title(f'Repository-Klassifikationen für {language}')
        plt.xticks(rotation=45, ha='right')

        # Werte über die Balken schreiben
        for bar, count in zip(bars, counts):
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.1, int(count), ha='center', va='bottom')

        plt.tight_layout()

        # Diagramm speichern
        safe_language_name = language.replace(" ", "_").replace("/", "_")
        output_file = output_dir / f"classification_{safe_language_name}.png"  # .pdf
        plt.savefig(output_file)
        plt.close()


def plot_cc_consistency_per_language(analysis_by_language, output_dir):
    """
    Plottet die CC-Konsistenz pro Sprache.

    Args:
        analysis_by_language (dict): Analysedaten gruppiert nach Sprache.
        output_dir (Path): Verzeichnis zum Speichern des Plots.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    languages = list(analysis_by_language.keys())
    cc_ratios = [analysis_by_language[lang]['cc_commit_ratio'] for lang in languages]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(languages, cc_ratios, color='#87CEEB')
    plt.xlabel('Programmiersprachen')
    plt.ylabel('CC Commit Ratio (%)')
    plt.title('CC-Konsistenz pro Programmiersprache')
    plt.xticks(rotation=45, ha='right')

    # Werte über die Balken schreiben
    for bar, ratio in zip(bars, cc_ratios):
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, yval + 1, f'{ratio:.1f}%', ha='center', va='bottom')

    plt.tight_layout()
    # Plot speichern
    output_file = output_dir / f"cc_consistency_per_language.png"
    plt.savefig(output_file)
    plt.close()


def plot_commit_type_distribution_per_language(analysis_by_language, output_dir, top_n=10):
    """
    Plottet die Commit-Typ-Verteilung pro Programmiersprache.

    Args:
        analysis_by_language (dict): Analysedaten gruppiert nach Sprache.
        output_dir (Path): Verzeichnis zum Speichern der Plots.
        top_n (int): Anzahl der Top-Typen, die geplottet werden sollen.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for language, data in analysis_by_language.items():
        type_distribution = data['type_distribution']

        # Sortiere die Typen nach Häufigkeit
        sorted_types = sorted(type_distribution.items(), key=lambda item: item[1], reverse=True)
        types = [item[0] for item in sorted_types[:top_n]]
        counts = [item[1] for item in sorted_types[:top_n]]

        plt.figure(figsize=(10, 6))
        bars = plt.bar(types, counts, color='#87CEEB')
        plt.xlabel('Commit-Typen')
        plt.ylabel('Häufigkeit')
        plt.title(f'Commit-Typ-Verteilung für {language}')
        plt.xticks(rotation=45, ha='right')

        # Werte über die Balken schreiben
        for bar, count in zip(bars, counts):
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.1, int(count), ha='center', va='bottom')

        plt.tight_layout()
        # Plot speichern
        safe_language_name = language.replace(" ", "_").replace("/", "_")
        output_file = output_dir / f"commit_type_distribution_{safe_language_name}.png"
        plt.savefig(output_file)
        plt.close()


def plot_commit_type_distribution(analysis_by_language, output_dir):
    """
    Plottet die Commit-Typ-Verteilung pro Repository für jede Sprache.

    Args:
        analysis_by_language (dict): Analysedaten gruppiert nach Sprache.
        output_dir (Path): Verzeichnis zum Speichern der Plots.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for language, analyses in analysis_by_language.items():
        for result in analyses:
            repo_name = result['repo_name']
            type_distribution = result['type_distribution']

            types = list(type_distribution.keys())
            counts = list(type_distribution.values())

            plt.figure(figsize=(8, 6))
            bars = plt.bar(types, counts, color='#87CEEB')
            plt.xlabel('Commit-Typen')
            plt.ylabel('Häufigkeit')
            plt.title(f'Commit-Typ-Verteilung für {repo_name} ({language})')
            plt.xticks(rotation=45, ha='right')

            # Werte über die Balken schreiben
            for bar, count in zip(bars, counts):
                yval = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.1, int(count), ha='center', va='bottom')

            plt.tight_layout()
            # Plot speichern
            safe_repo_name = repo_name.replace(" ", "_").replace("/", "_")
            safe_language_name = language.replace(" ", "_").replace("/", "_")
            output_file = output_dir / f"commit_types_{safe_language_name}_{safe_repo_name}.png"
            plt.savefig(output_file)
            plt.close()


def plot_adoption_rate(adopted_repos, total_repos):
    not_adopted = total_repos - adopted_repos

    labels = ['CC-Adoptiert', 'Nicht CC-Adoptiert']
    sizes = [adopted_repos, not_adopted]
    colors = ['green', 'red']

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title('Adoptionsrate von Conventional Commits')
    plt.axis('equal')
    plt.savefig(ROOT / "results" / "diagrams" / 'overall_cc_adoptionsrate.png')
    plt.show()


def plot_aggregate_commit_types(total_cc_type_distribution, string):
    # Sortiere die Typen nach Häufigkeit
    types = list(total_cc_type_distribution.keys())
    counts = [total_cc_type_distribution[ctype] for ctype in types]
    data = sorted(zip(counts, types), reverse=True)
    counts_sorted, types_sorted = zip(*data[:30])

    plt.figure(figsize=(10, 6))
    bars = plt.bar(types_sorted, counts_sorted, color='purple')
    plt.xlabel('Commit-Typ')
    plt.ylabel('Anzahl')
    plt.title('Gesamte Verteilung der Commit-Typen')
    plt.xticks(rotation=45)

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, int(yval), ha='center', va='bottom',
                 fontsize=7)  # Schriftgröße anpassen

    plt.tight_layout()
    plt.savefig(ROOT / "results" / "diagrams" / f'overall_{string}.png')
    plt.show()


def plot_adoption_rate_by_language(adoption_rates):
    languages = list(adoption_rates.keys())
    rates = [adoption_rates[lang] * 100 for lang in languages]

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


def plot_scatter(
        x: List[float],
        y: List[float],
        title: str,
        xlabel: str,
        ylabel: str,
        trendline: bool = True,
        correlation: bool = True,
        colors: Optional[List[str]] = None,
        save_path: Optional[Path] = None,
        show: bool = True
):
    """
    Generiert einen Scatter-Plot und optional eine Trendlinie sowie den Korrelationskoeffizienten.

    Args:
        x (List[float]): Daten für die x-Achse.
        y (List[float]): Daten für die y-Achse.
        title (str): Titel des Diagramms.
        xlabel (str): Beschriftung der x-Achse.
        ylabel (str): Beschriftung der y-Achse.
        trendline (bool, optional): Ob eine Trendlinie hinzugefügt werden soll. Standard ist True.
        correlation (bool, optional): Ob der Korrelationskoeffizient angezeigt werden soll. Standard ist True.
        colors (List[str], optional): Farben der Punkte. Standard ist Blau.
        save_path (Path, optional): Pfad zum Speichern des Diagramms.
        show (bool, optional): Ob das Diagramm angezeigt werden soll. Standard ist True.
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, color=colors if colors else 'blue', alpha=0.6, edgecolors='w', linewidth=0.5)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)

    # Trendlinie hinzufügen
    if trendline and len(x) > 1:
        m, b = np.polyfit(x, y, 1)
        plt.plot(x, [m * xi + b for xi in x], color='red', linewidth=2, label='Trendlinie')

    # Korrelationskoeffizienten berechnen und anzeigen
    if correlation and len(x) > 1:
        corr_coef = np.corrcoef(x, y)[0, 1]
        plt.annotate(f'Korrelationskoeffizient: {corr_coef:.2f}',
                     xy=(0.05, 0.95), xycoords='axes fraction',
                     fontsize=12, ha='left', va='top',
                     bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5))

    if trendline and len(x) > 1:
        plt.legend()

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
        print(f"Scatter-Plot gespeichert: {save_path}")
    if show:
        plt.show()
    plt.close()


def plot_size_vs_cc_usage(
        summaries: List[Dict],
        save_path: Optional[Path] = None,
        show: bool = True
):
    """
    Berechnet den Zusammenhang zwischen Repository-Größe und CC-Nutzung und plottet diesen.

    Args:
        summaries (List[Dict]): Liste der Analysezusammenfassungen für jedes Repository.
        save_path (Path, optional): Pfad zum Speichern des Scatter-Plots. Standard ist None.
        show (bool, optional): Ob der Scatter-Plot angezeigt werden soll. Standard ist True.

    Returns:
        None
    """
    sizes = []
    cc_usages = []

    for summary in summaries:
        size = summary.get('size')
        total_commits = summary.get('total_commits', 0)
        conventional_commits = summary.get('cc_type_commits', 0)

        if size is None or total_commits == 0:
            print(f"Repository {summary.get('repo_name', 'Unknown')} hat keine gültige Größe oder keine Commits.")
            continue

        cc_usage_percentage = (conventional_commits / total_commits) * 100
        sizes.append(size)
        cc_usages.append(cc_usage_percentage)

    if not sizes or not cc_usages:
        print.error("Keine gültigen Daten zum Plotten verfügbar.")
        return

    title = "Zusammenhang zwischen Repository-Größe und CC-Nutzung"
    xlabel = "Repository-Größe (KB)"
    ylabel = "CC-Nutzung (%)"

    plot_scatter(
        x=sizes,
        y=cc_usages,
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        trendline=True,
        correlation=True,
        colors=None,  # Optional: Passe die Farbe der Punkte an
        save_path=save_path,
        show=show
    )


import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Optional
import logging


def plot_size_vs_cc_usage_stripplot(
        summaries: List[Dict],
        save_path: Optional[Path] = None,
        show: bool = True
):
    """
    Erstellt einen Strip Plot, der den Zusammenhang zwischen Repository-Größe und CC-Nutzung zeigt.
    Die y-Achse repräsentiert die Repository-Größe, und die x-Achse zeigt den Konventionalitätsstatus.

    Args:
        summaries (List[Dict]): Liste der Analysezusammenfassungen für jedes Repository.
        save_path (Path, optional): Pfad zum Speichern des Plots. Standard ist None.
        show (bool, optional): Ob der Plot angezeigt werden soll. Standard ist True.

    Returns:
        None
    """
    # Filtere Repositories mit gültiger Größe und Commits
    filtered_summaries = [
        summary for summary in summaries
        if summary.get('size') is not None
    ]

    if not filtered_summaries:
        logging.error("Keine gültigen Daten zum Plotten verfügbar.")
        return

    # Erstelle ein DataFrame mit den Daten
    df = pd.DataFrame({
        'size': [summary['size'] for summary in filtered_summaries],
        'cc_adoption': ['Conventional' if summary.get('cc_adoption_date') else 'Non-Conventional' for summary in
                        filtered_summaries]
    })

    # Sortiere das DataFrame nach Größe
    df = df.sort_values(by='size')

    # Erstelle den Strip Plot
    plt.figure(figsize=(10, 8))
    sns.stripplot(x='size', y='cc_adoption', data=df, jitter=True, alpha=0.6,
                  palette={'Conventional': 'yellowgreen', 'Non-Conventional': 'lightyellow'})
    plt.title("Zusammenhang zwischen Repository-Größe und CC-Nutzung (Strip Plot)")
    plt.xlabel("CC Nutzung")
    plt.ylabel("Repository-Größe (KB)")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight')
        logging.info(f"Strip Plot gespeichert: {save_path}")
    if show:
        plt.show()
    plt.close()

# if __name__ == "__main__":
# Pfade zu deinen Daten
# RESULTS_DIR = ROOT / "results" / "commit_messages"  # Ersetze durch deinen tatsächlichen Pfad
# classification_file = ROOT / "results" / "repository_classifications.json"
# OUTPUT_DIR = ROOT / "results"  # Ersetze durch dein gewünschtes Ausgabeverzeichnis
#
# # Klassifikationen laden
# classifications = load_classifications(classification_file)
#
# # Repositories filtern
# filtered_repos = filter_repositories(classifications, target_classification='nutzen CC und als Vorgabe erkennbar')
#
# # Repositories analysieren
# analysis_by_language = analyze_repositories_by_language(filtered_repos, RESULTS_DIR)
#
# # CC-Konsistenz plotten
# cc_consistency_output_dir = OUTPUT_DIR / "cc_consistency"
# plot_cc_consistency_per_language(analysis_by_language, cc_consistency_output_dir)
#
# # Commit-Typ-Verteilung plotten
# commit_type_output_dir = OUTPUT_DIR / "commit_type_distribution"
# plot_commit_type_distribution_per_language(analysis_by_language, commit_type_output_dir)
