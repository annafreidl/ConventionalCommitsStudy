from collections import Counter
import matplotlib.pyplot as plt
from analysis import is_conventional_commit, save_custom_types, CUSTOM_TYPES_FILE_PATH, custom_types
from json_utils import load_json


def visualize_repo_commits(commits_from_json, repo_name):
    """
    Visualisiert Commit-Daten eines Repositories basierend auf einer JSON-Datei.
    """

    visualize_cc_ratio(commits_from_json, repo_name)
    visualize_custom_type_word_counts(CUSTOM_TYPES_FILE_PATH)


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
    plt.axis('equal')  # Kreisförmig anzeigen
    plt.show()


def visualize_cc_ratio(commits, project_name):
    """
    Erstellt ein Kreisdiagramm, das das Verhältnis von konventionellen zu nicht-konventionellen Commits visualisiert.
    """
    conventional_count = sum(is_conventional_commit(commit['message']) for commit in commits)
    unconventional_count = len(commits) - conventional_count

    print("Custom Types:", set(custom_types))

    # Speichere die custom commit types
    save_custom_types(custom_types)

    # Kreisdiagramm visualisieren
    visualize_pie_chart(conventional_count, unconventional_count, project_name)


def visualize_custom_type_word_counts(json_file_path):
    """
    Visualisiert die 20 häufigsten Wörter in einer JSON-Datei.
    """
    data = load_json(json_file_path)
    if data is None:
        return

    word_counts = Counter(data)
    most_common_words = word_counts.most_common(20)

    if not most_common_words:
        print("Keine Wörter zum Anzeigen gefunden.")
        return

    words, counts = zip(*most_common_words)

    # Balkendiagramm erstellen
    plt.figure(figsize=(10, 6))
    plt.bar(words, counts, color='#87CEEB')
    plt.xlabel('Wörter')
    plt.ylabel('Häufigkeit')
    plt.title('Die 20 häufigsten custom types')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()


# Aufruf der Funktion im Hauptteil
if __name__ == "__main__":
    visualize_custom_type_word_counts('C:\\Users\\annaf\\PycharmProjects\\Bachelorarbeit\\src\\results\\custom_types.json')
