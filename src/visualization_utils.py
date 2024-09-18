import matplotlib.pyplot as plt
from json_utils import load_json

def visualize_repo_commits(json_file_path, repo_name):
    """
    Visualisiert Commit-Daten eines Repositories basierend auf einer JSON-Datei.
    """
    data = load_json(json_file_path)
    if data is None:
        print(f"Fehler beim Laden der JSON-Datei für {repo_name}.")
        return

    analysis_summary = data.get('analysis_summary', {})
    custom_type_distribution = analysis_summary.get('custom_type_distribution', {})
    cc_type_distribution = analysis_summary.get('cc_type_distribution', {})

    # Visualisierungsfunktionen aufrufen
    visualize_cc_ratio(analysis_summary, repo_name)
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


# Aufruf der Funktion im Hauptteil
if __name__ == "__main__":
    visualize_type_distribution('C:\\Users\\annaf\\PycharmProjects\\Bachelorarbeit\\src\\results\\custom_types.json')
