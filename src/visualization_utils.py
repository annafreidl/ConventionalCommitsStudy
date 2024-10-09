import json
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt

from analyzer import filter_repositories, analyze_repositories_by_language
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


# Aufruf der Funktion im Hauptteil
# if __name__ == "__main__":
#     visualize_type_distribution('C:\\Users\\annaf\\PycharmProjects\\Bachelorarbeit\\src\\results\\custom_types.json')

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
        output_file = output_dir / f"classification_{safe_language_name}.png"
        plt.savefig(output_file)
        plt.close()


# visualization_utils.py

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
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1, f'{ratio:.1f}%', ha='center', va='bottom')

    plt.tight_layout()
    # Plot speichern
    output_file = output_dir / f"cc_consistency_per_language.png"
    plt.savefig(output_file)
    plt.close()

# visualization_utils.py

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
            plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, int(count), ha='center', va='bottom')

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
                plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, int(count), ha='center', va='bottom')

            plt.tight_layout()
            # Plot speichern
            safe_repo_name = repo_name.replace(" ", "_").replace("/", "_")
            safe_language_name = language.replace(" ", "_").replace("/", "_")
            output_file = output_dir / f"commit_types_{safe_language_name}_{safe_repo_name}.png"
            plt.savefig(output_file)
            plt.close()


if __name__ == "__main__":
    # Pfade zu deinen Daten
    RESULTS_DIR = ROOT / "results" / "commit_messages" # Ersetze durch deinen tatsächlichen Pfad
    classification_file = ROOT / "results" / "repository_classifications.json"
    OUTPUT_DIR = ROOT / "results"  # Ersetze durch dein gewünschtes Ausgabeverzeichnis

    # Klassifikationen laden
    classifications = load_classifications(classification_file)

    # Repositories filtern
    filtered_repos = filter_repositories(classifications, target_classification='nutzen CC und als Vorgabe erkennbar')

    # Repositories analysieren
    analysis_by_language = analyze_repositories_by_language(filtered_repos, RESULTS_DIR)

    # CC-Konsistenz plotten
    cc_consistency_output_dir = OUTPUT_DIR / "cc_consistency"
    plot_cc_consistency_per_language(analysis_by_language, cc_consistency_output_dir)

    # Commit-Typ-Verteilung plotten
    commit_type_output_dir = OUTPUT_DIR / "commit_type_distribution"
    plot_commit_type_distribution_per_language(analysis_by_language, commit_type_output_dir)
