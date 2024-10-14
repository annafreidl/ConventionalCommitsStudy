from pathlib import Path

import matplotlib.pyplot as plt

from constants import CHUNK_SIZE_PERCENT, NUM_CHUNKS, MIN_CC_PERCENTAGE
from data_saver import load_from_json, load_dataset
from repository_manager import clone_repository


def chunk_data(commits, ganze_chunks, num_chunks=NUM_CHUNKS):
    zahl_der_commits = len(commits)
    rest_chunk = zahl_der_commits % ganze_chunks

    for i in range(0, num_chunks * ganze_chunks, ganze_chunks):
        if zahl_der_commits - i < 2 * ganze_chunks:
            yield commits[i:i + ganze_chunks + rest_chunk]
            break
        else:
            yield commits[i:i + ganze_chunks]


def analyse_commit_chunks(data, chunk_size=CHUNK_SIZE_PERCENT):
    # Extraktion aus data (Commit-Daten)
    commits = data.get("commits", {})
    analysis_summary = data.get("analysis_summary", {})

    # Extraktion aus analysis_summary (Analyse-Daten)
    cc_type_commits = analysis_summary.get("cc_type_commits", {})
    total_commits = analysis_summary.get("total_commits", 0)

    # Berechnung der Mindestgrenze
    mindestgrenze_rel = cc_type_commits / total_commits
    mindesgrenze_rel_erfüllt = mindestgrenze_rel >= 0.05
    print(f"Mindestgrenze (relativ): {mindestgrenze_rel}")
    print(f"Mindestgrenze (relativ): {mindesgrenze_rel_erfüllt}")

    mindestgrenze_abs = cc_type_commits > 200
    print(f"Mindestgrenze (absolut): {mindestgrenze_abs}")
    print(f"Anzahl CCCommits: {cc_type_commits}")

    if mindestgrenze_rel > 0.05 and mindestgrenze_abs:
        print("Beide Mindestgrenzen sind erfüllt")

        # Berechnung der Chunkgrößen
        # Standard - Chunkgröße
        ganze_chunks = total_commits // (1 / chunk_size)
        rest_chunk = total_commits % ganze_chunks
        print(f"Größe ganzer Chunks: {ganze_chunks}")
        print(f"Größe Rest-Chunk: {rest_chunk}")

        list_chunk_cc_rates = []

        for chunk in chunk_data(commits, int(ganze_chunks), num_chunks=NUM_CHUNKS):

            anzahl_cc_commits = 0
            for i in range(len(chunk)):
                if chunk[i].get("cc_type") is not None:
                    anzahl_cc_commits += 1

            chunk_cc_rate = anzahl_cc_commits / len(chunk)
            gerundete_chunk_cc_rate = round(chunk_cc_rate, 2)
            list_chunk_cc_rates.append(gerundete_chunk_cc_rate)

        list_reversed = list_chunk_cc_rates[::-1]
        cc_chunks = find_cc_chunk_adoption_date(list_reversed)
        if cc_chunks != -1:
            print(f"Konsequente CC Nutzung ab {cc_chunks}")
            if analysis_summary.get("cc_adoption_date") is not None:
                print(f"Unverändertes Ergebnis")
            else: print(f"BREAKING CHANGE: CC-Nutzung erkannt")
            return True
        else:
            if analysis_summary.get("cc_adoption_date") is not None:
                print(f"BREAKING CHANGE: CC-Nutzung nicht mehr erkannt")
                print(f"adoption_date: {analysis_summary.get('cc_adoption_date')}")
            else: print(f"Unverändertes Ergebnis")
            print("Keine konsequente CC Nutzung")
            return False
        # visualize_commit_chunks(list_reversed)

    else:
        print("Zu wenige Commits für eine Analyse")
        return False


def visualize_commit_chunks(chunkliste):
    plt.title = ("Commit Chunks")
    percent = [wert * 100 for wert in chunkliste]

    # Erstelle die x-Achsen-Beschriftungen (1, 2, 3, ...)
    x_achsen = list(range(0, len(percent)))

    # Erstelle das Balkendiagramm
    plt.figure(figsize=(10, 6))
    bars = plt.bar(x_achsen, percent, color='skyblue')

    # Setze die y-Achse von 0% bis 100%
    plt.ylim(0, 100)

    # Beschrifte die Achsen
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


def find_cc_chunk_adoption_date(pieplist):
    last_cc_index = -1

    # Anzahl der CC-Chunks in der Liste
    anzahl_cc_chunks = count_chunks(pieplist)
    print(f"Anzahl existierender CC-Chunks: {anzahl_cc_chunks}")

    # Wenn keine CC-Chunks, dann gibt es keinen Adoption-Zeitpunkt
    if anzahl_cc_chunks == 0:
        return last_cc_index

    # Durchlaufe die Liste von hinten nach vorne
    reversed_list = pieplist[::-1]

    for i in range(len(reversed_list)):

        # wenn Element >= 0.8, dann suche weiter
        if reversed_list[i] >= MIN_CC_PERCENTAGE:
            last_cc_index = i

        # wenn Element < 0.8, dann beende Suche nach dem letzten Chunk
        else:

            if last_cc_index < anzahl_cc_chunks - 1:

                first_cc_index = 0
                for x in range(len(pieplist)):
                    if pieplist[x] < MIN_CC_PERCENTAGE:
                        first_cc_index = x + 1
                    else:
                        print(f"Erster 80% CC-Chunk ist bei: {first_cc_index}")
                        break

            if last_cc_index == -1:

                print(f"Kein CC Repo")

                if anzahl_cc_chunks > 1:
                    cc_endet = 0
                    for u in range(len(reversed_list)):
                        if reversed_list[u] > MIN_CC_PERCENTAGE:
                            cc_endet = u
                            print(
                                f"Letzter 80% Chunk, falls nicht konsequent bis heute: {len(pieplist) - cc_endet - 1}")
                            break

                return last_cc_index
            else:
                return len(pieplist) - last_cc_index - 1

    return len(pieplist) - last_cc_index


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
        print("Klonen abgeschlosen")

        data = load_from_json(json_file_path)
        print("Daten geladen")

        if data.get("analysis_summary", {}).get("total_commits", 0) > 0:
            cc_anwendung = analyse_commit_chunks(data)
            if cc_anwendung:
                cc_anwendungen += 1

            print("Analyse abgeschlossen\n")
        else:
            print("Keine Commits vorhanden\n")

    print(f"Anzahl CC-Anwendungen: {cc_anwendungen}")
