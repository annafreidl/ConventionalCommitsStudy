# analyzer.py

# Standardbibliotheken
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from collections import defaultdict, Counter
from datetime import datetime
import json
import math
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Lokale Module
from constants import MIN_CC_PERCENTAGE, MIN_CC_COMMITS
from visualization_utils import (
    plot_adoption_rate,
    plot_aggregate_commit_types,
    plot_adoption_rate_by_language
)


def classify_repository(analysis_summary, using_cc):
    """
    Klassifiziert das Repository basierend auf der Analyse und der CC-Nutzung.

    Args:
        analysis_summary (dict): Zusammenfassung der Analyse.
        using_cc (bool): Ob CC verwendet wird.

    Returns:
        str: Klassifikation des Repositories.
    """

    adoption_date_exists = analysis_summary.get("cc_adoption_date") is not None

    classification_map = {
        (False, False): "nicht conventional",
        (False, True): "nutzen CC, aber nicht als Vorgabe erkennbar",
        (True, True): "nutzen CC und als Vorgabe erkennbar",
        (True, False): "Erwaehnung von CC, aber wird nicht genutzt"
    }

    return classification_map.get((using_cc, adoption_date_exists), "nicht eindeutig klassifizierbar")


def search_for_cc_indications(repo_instance):
    """
    Überprüft, ob ein Repository die Conventional Commits-Konvention verwendet,
    basierend auf spezifischen Konfigurationsdateien, Abhängigkeiten und Git Hooks.

    Args:
        repo_instance (Repo)

    Returns:
        bool: True, wenn Conventional Commits verwendet werden, sonst False.
    """
    local_path = Path(repo_instance.working_tree_dir)
    print(f"Überprüfe Repository: {local_path}")

    # Indikator, ob Hinweise gefunden wurden
    cc_detected = False

    # 1. Überprüfung der package.json
    package_json_path = local_path / 'package.json'
    if package_json_path.exists():
        cc_detected = check_package_json(package_json_path) or cc_detected

    # 2. Überprüfung spezifischer Konfigurationsdateien
    cc_detected = check_cc_configuration_files(local_path) or cc_detected

    # 3. Überprüfung der Git Hooks
    cc_detected = check_git_hooks(local_path) or cc_detected

    # 4. Durchsicht der Dokumentation und wiki
    cc_detected = check_documentation_for_cc(local_path) or cc_detected

    if cc_detected:
        print("Hinweise auf die Verwendung der Conventional Commit Konvention gefunden.")
        return True
    else:
        print("Keine Hinweise auf die Verwendung der Conventional Commit Konvention gefunden.")
        return False


def check_package_json(package_json_path):
    """
    Überprüft die package.json auf Abhängigkeiten, die auf die Verwendung von Conventional Commits hinweisen.

    Args:
        package_json_path (Path): Pfad zur package.json Datei.

    Returns:
        bool: True, wenn Hinweise gefunden wurden, sonst False.
    """
    try:
        with open(package_json_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
            dependencies = data.get('dependencies', {})
            dev_dependencies = data.get('devDependencies', {})
            all_dependencies = {**dependencies, **dev_dependencies}
            cc_packages = [
                "commitizen",
                "cz-conventional-changelog",
                "@commitlint/cli",
                "@commitlint/config-conventional",
                "standard-version",
                "semantic-release"
            ]
            found_packages = []
            for dep in cc_packages:
                if dep in all_dependencies:
                    found_packages.append(dep)

            if found_packages:
                print(f"CC-bezogene Abhängigkeiten gefunden in package.json: {found_packages}")
                return True
    except Exception as e:
        print(f"Fehler beim Lesen der package.json: {e}")
    return False


def check_cc_configuration_files(local_path):
    """
    Überprüft, ob spezifische Konfigurationsdateien vorhanden sind, die auf die Verwendung von CC hinweisen.

    Args:
        local_path (Path): Pfad zum lokalen Repository.

    Returns:
        bool: True, wenn Hinweise gefunden wurden, sonst False.
    """
    cc_config_files = [
        'commitlint.config.js',
        '.commitlintrc',
        '.commitlintrc.js',
        '.commitlintrc.json',
        '.cz-config.js',
        '.czrc',
        '.versionrc'
    ]

    for config_file in cc_config_files:
        config_path = local_path / config_file
        if config_path.exists():
            print(f"Konfigurationsdatei gefunden: {config_file}")
            return True
    return False


def check_git_hooks(local_path):
    """
    Überprüft, ob Git Hooks eingerichtet sind, die auf die Verwendung von CC hinweisen.

    Args:
        local_path (Path): Pfad zum lokalen Repository.

    Returns:
        bool: True, wenn Hinweise gefunden wurden, sonst False.
    """
    git_hooks_path = local_path / '.husky'
    if git_hooks_path.exists() and git_hooks_path.is_dir():
        for hook_file in git_hooks_path.iterdir():
            if hook_file.is_file():
                with open(hook_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'commitlint' in content or 'commitizen' in content:
                        print(f"Git Hook mit CC-Referenz gefunden: {hook_file.name}")
                        return True
    else:
        # Alternative: Überprüfung der .git/hooks Verzeichnis
        git_hooks_path = local_path / '.git' / 'hooks'
        if git_hooks_path.exists() and git_hooks_path.is_dir():
            for hook_file in git_hooks_path.iterdir():
                if hook_file.is_file() and not hook_file.name.endswith('.sample'):
                    with open(hook_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if 'commitlint' in content or 'commitizen' in content:
                            print(f"Git Hook mit CC-Referenz gefunden: {hook_file.name}")
                            return True
    return False


def check_documentation_for_cc(local_path):
    """
    Durchsucht Dokumentationsdateien und das Wiki nach Erwähnungen der Conventional Commit Konvention.

    Args:
        local_path (Path): Pfad zum lokalen Repository.

    Returns:
        bool: True, wenn Hinweise gefunden wurden, sonst False.
    """
    doc_files = [
        'README.md',
        'CONTRIBUTING.md',
        'DEVELOPING.md'
    ]

    keywords = [
        "Conventional Commits",
        "Conventional Commit",
        "Conventional Changelog",
        "Commit Message Convention",
        "Commit Guidelines",
        "commitizen",
        "commitlint",
        "standard-version",
        "semantic-release"
    ]

    # Durchsuchen der Dokumentationsdateien im Hauptverzeichnis
    for doc_file in doc_files:
        doc_path = local_path / doc_file
        if doc_path.exists():
            with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for keyword in keywords:
                    if re.search(r'\b' + re.escape(keyword) + r'\b', content, re.IGNORECASE):
                        print(f"Keyword '{keyword}' gefunden in {doc_file}")
                        return True  # Hinweise gefunden

    # Durchsuchen des Wikis
    wiki_dir = local_path / '.wiki'
    if wiki_dir.exists():
        for root, dirs, files in os.walk(wiki_dir):
            for file in files:
                if file.endswith(('.md', '.txt', '.rst', '.adoc')):  # Textbasierte Dateien
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            for keyword in keywords:
                                if re.search(r'\b' + re.escape(keyword) + r'\b', content, re.IGNORECASE):
                                    print(f"Keyword '{keyword}' gefunden in Wiki-Datei: {file_path}")
                                    return True  # Hinweise gefunden
                    except Exception as e:
                        print(f"Fehler beim Lesen der Datei {file_path}: {e}")
    else:
        print("Kein Wiki-Verzeichnis gefunden. Überspringe die Wiki-Prüfung.")

    return False  # Keine Hinweise gefunden


def find_cc_adoption_date(commits, min_cc_percentage=MIN_CC_PERCENTAGE, min_cc_commits=MIN_CC_COMMITS):
    total_commits = len(commits)
    if total_commits == 0:
        return None  # Keine Commits verfügbar
    # Umkehren der Commit-Liste, sodass der älteste Commit an Index 0 steht
    commits_reversed = commits[::-1]

    # Kumulative Summe der konventionellen Commits berechnen
    cum_conventional_commits = [0] * (total_commits + 1)
    for i in range(1, total_commits + 1):
        is_conv = 1 if commits_reversed[i - 1].get("cc_type") else 0
        cum_conventional_commits[i] = cum_conventional_commits[i - 1] + is_conv

    # Minimale Anzahl verbleibender Commits berechnen
    min_remaining_commits = int(math.ceil(min_cc_commits / min_cc_percentage))

    # Iterieren über die Commits
    for i in range(total_commits):
        num_remaining_commits = total_commits - i

        # Überprüfe, ob genügend verbleibende Commits vorhanden sind
        if num_remaining_commits < min_remaining_commits:
            break  # Nicht genug verbleibende Commits

        conventional_commits = cum_conventional_commits[total_commits] - cum_conventional_commits[i]
        cc_percentage = conventional_commits / num_remaining_commits

        # Überprüfe, ob sowohl der Mindestprozentsatz als auch die Mindestanzahl an konventionellen Commits erreicht
        # sind
        if cc_percentage >= min_cc_percentage and conventional_commits >= min_cc_commits:
            return commits_reversed[i]['committed_datetime'][:10]  # Rückgabe des Datums ab diesem Commit

    return None  # Nicht genug konventionelle Commits gefunden


def calculate_monthly_conventional_commits(commits):
    """
    Berechnet den prozentualen Anteil der konventionellen Commits mit cc_type und custom_type für jeden Monat.

    Args:
        commits (list): Liste der angereicherten Commits.

    Returns:
        tuple: Zwei Dictionaries:
              - Anteil der Commits mit cc_type pro Monat
              - Anteil der Commits mit custom_type pro Monat
    """
    # Dictionary, um die Anzahl der Commits pro Monat zu speichern
    monthly_commits = defaultdict(
        lambda: {"total": 0, "conventional_with_cc_type": 0, "conventional_with_custom_type": 0})

    # Commits nach Monat gruppieren und konventionelle Commits mit cc_type und custom_type zählen
    for commit in commits:
        commit_date_str = commit.get("committed_datetime")
        cc_type = commit.get("cc_type", None)
        custom_type = commit.get("custom_type", None)

        # Sicherstellen, dass commit_date_str nicht None ist
        if not commit_date_str:
            continue  # Überspringe Commits ohne Datum

        commit_date = datetime.fromisoformat(commit_date_str)
        year_month = commit_date.strftime("%Y-%m")

        # Zähle den Commit für den jeweiligen Monat
        monthly_commits[year_month]["total"] += 1
        if cc_type:
            monthly_commits[year_month]["conventional_with_cc_type"] += 1
        if custom_type:
            monthly_commits[year_month]["conventional_with_custom_type"] += 1

    # Berechne den prozentualen Anteil pro Monat für cc_type und custom_type
    monthly_cc_type_percentage = {
        month: (counts["conventional_with_cc_type"] / counts["total"]) * 100 if counts["total"] > 0 else 0
        for month, counts in monthly_commits.items()
    }

    monthly_custom_type_percentage = {
        month: (counts["conventional_with_custom_type"] / counts["total"]) * 100 if counts["total"] > 0 else 0
        for month, counts in monthly_commits.items()
    }

    return monthly_cc_type_percentage, monthly_custom_type_percentage


def filter_repositories(classifications, target_classification='nutzen CC und als Vorgabe erkennbar'):
    """
    Filtert Repositories basierend auf der Zielklassifikation.

    Args:
        classifications (dict): Dictionary mit Sprache als Schlüssel und Repositories als Wert.
        target_classification (str): Die Klassifikation, nach der gefiltert werden soll.

    Returns:
        dict: Gefiltertes Dictionary mit Sprache als Schlüssel und Liste von Repository-Namen als Wert.
    """
    filtered_repos = {}

    for language, repos in classifications.items():
        matching_repos = [repo_name for repo_name, classification in repos.items() if
                          classification == target_classification]
        if matching_repos:
            filtered_repos[language] = matching_repos

    return filtered_repos


import datetime


def analyze_repository_from_existing_data(repo_name, results_dir):
    """
    Analysiert die vorhandenen Commit-Daten eines Repositories hinsichtlich CC-Konsistenz und Commit-Typ-Verteilung,
    berücksichtigt dabei nur Commits nach dem cc_adoption_date.

    Args:
        repo_name (str): Name des Repositories.
        results_dir (Path): Pfad zum Verzeichnis mit den JSON-Daten der Repositories.

    Returns:
        dict: Analyseergebnisse, einschließlich CC-Konsistenz und Commit-Typ-Verteilung.
    """
    # Lade die angereicherten Commit-Daten
    repo_json_file = results_dir / f"{repo_name}_commit_messages.json"
    if not repo_json_file.exists():
        print(f"Commit-Daten für Repository {repo_name} nicht gefunden.")
        return None

    with open(repo_json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    commits = data.get('commits', [])
    analysis_summary = data.get('analysis_summary', {})

    cc_adoption_date_str = analysis_summary.get('cc_adoption_date')
    if not cc_adoption_date_str:
        print(f"CC-Einführungsdatum für Repository {repo_name} nicht gefunden.")
        return None

    # Versuche, das Datum zu parsen
    try:
        # Wenn das Datum das Zeitformat enthält
        cc_adoption_date = datetime.datetime.strptime(cc_adoption_date_str, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        try:
            # Wenn das Datum nur das Datum ohne Zeit enthält
            cc_adoption_date = datetime.datetime.strptime(cc_adoption_date_str, "%Y-%m-%d")
        except ValueError:
            print(f"Ungültiges Datumsformat für cc_adoption_date in Repository {repo_name}: {cc_adoption_date_str}")
            return None

    # Filtere die Commits nach cc_adoption_date
    commits_after_adoption = []
    for commit in commits:
        commit_date_str = commit.get('committed_datetime')
        commit_date = datetime.datetime.strptime(commit_date_str, "%Y-%m-%dT%H:%M:%S")
        if commit_date >= cc_adoption_date:
            commits_after_adoption.append(commit)

    total_commits = len(commits_after_adoption)
    if total_commits == 0:
        print(f"Keine Commits nach CC-Einführung für Repository {repo_name} gefunden.")
        return None

    # CC-Konsistenz analysieren
    conventional_commits = [commit for commit in commits_after_adoption if commit.get('is_conventional')]
    cc_commit_ratio = len(conventional_commits) / total_commits * 100

    # Commit-Typ-Verteilung analysieren
    cc_types = [commit.get('cc_type') for commit in conventional_commits if commit.get('cc_type')]
    custom_types = [commit.get('custom_type') for commit in conventional_commits if commit.get('custom_type')]

    from collections import Counter
    cc_type_distribution = Counter(cc_types)
    custom_type_distribution = Counter(custom_types)

    # Zusammenführen der CC-Typen und Custom-Typen
    type_distribution = cc_type_distribution + custom_type_distribution

    # Entferne None-Schlüssel
    type_distribution.pop(None, None)

    analysis_results = {
        'repo_name': repo_name,
        'total_commits': total_commits,
        'conventional_commits': len(conventional_commits),
        'cc_commit_ratio': cc_commit_ratio,
        'type_distribution': dict(type_distribution)
    }

    return analysis_results


def analyze_repositories_by_language(filtered_repos: Dict[str, List[str]], results_dir: Path):
    """
    Analysiert Repositories nach Sprache unter Verwendung vorhandener Daten und aggregiert die Type Distribution pro Sprache.

    Args:
        filtered_repos (dict): Gefilterte Repositories mit Sprache als Schlüssel und Repository-Namen als Wert.
        results_dir (Path): Pfad zum Verzeichnis mit den JSON-Daten der Repositories.

    Returns:
        dict: Analysedaten mit Sprache als Schlüssel und Analyseergebnissen als Wert.
    """
    analysis_by_language = {}

    for language, repo_names in filtered_repos.items():
        total_commits_language = 0
        conventional_commits_language = 0
        type_distribution_language = Counter()

        for repo_name in repo_names:
            result = analyze_repository_from_existing_data(repo_name, results_dir)
            if result:
                total_commits_language += result['total_commits']
                conventional_commits_language += result['conventional_commits']
                type_distribution_language.update(result['type_distribution'])

        if total_commits_language > 0:
            cc_commit_ratio_language = (conventional_commits_language / total_commits_language) * 100
            analysis_by_language[language] = {
                'total_commits': total_commits_language,
                'conventional_commits': conventional_commits_language,
                'cc_commit_ratio': cc_commit_ratio_language,
                'type_distribution': dict(type_distribution_language)
            }

    return analysis_by_language


def calculate_adoption_rate(summaries):
    total_repos = len(summaries)
    adopted_repos = sum(1 for s in summaries if s.get('cc_adoption_date', 0) is not None)
    adoption_rate = adopted_repos / total_repos if total_repos > 0 else 0
    print(f"Gesamtzahl der Repositories: {total_repos}")
    print(f"Repositories mit CC-Nutzung: {adopted_repos}")
    print(f"Adoptionsrate: {adoption_rate:.2%}")

    plot_adoption_rate(adopted_repos, total_repos)


def aggregate_commit_types(summaries, string):
    total_cc_type_distribution = Counter(
        ctype
        for summary in summaries
        for ctype, count in summary.get(string, {}).items()
        for _ in range(count)
    )

    print("Gesamte CC-Typ-Verteilung:")
    for ctype, count in total_cc_type_distribution.items():
        print(f"{ctype}: {count}")

    plot_aggregate_commit_types(dict(total_cc_type_distribution), string)


def calculate_adoption_rate_by_language(summaries):
    language_stats = defaultdict(lambda: {'total_repos': 0, 'adopted_repos': 0})

    for summary in summaries:
        language = summary.get('language', 'Unknown')
        language_stats[language]['total_repos'] += 1
        if summary.get('cc_adoption_date') is not None:
            language_stats[language]['adopted_repos'] += 1

    adoption_rates = {
        language: (stats['adopted_repos'] / stats['total_repos'] * 100) if stats['total_repos'] > 0 else 0
        for language, stats in language_stats.items()
    }

    for language, rate in adoption_rates.items():
        print(f"Sprache: {language}")
        print(f"  Gesamtzahl der Repositories: {language_stats[language]['total_repos']}")
        print(f"  Repositories mit CC-Nutzung: {language_stats[language]['adopted_repos']}")
        print(f"  Adoptionsrate: {rate:.2f}%")
        print('-' * 40)

    plot_adoption_rate_by_language(adoption_rates)

    return adoption_rates


def size_vs_cc_usage(summaries):
    # Plot der Größe vs. CC-Nutzung
    data = []
    for summary in summaries:
        is_conventional = summary['cc_adoption_date'] is not None
        size = summary.get('size', 0)  # Standardgröße 0, falls nicht vorhanden
        data.append({
            'Repository': summary.get('repo_name', 'Unknown'),
            'Konventionell': 'Ja' if is_conventional else 'Nein',
            'Size': size
        })

    # Erstelle einen DataFrame
    df = pd.DataFrame(data)

    # Optional: Daten anzeigen
    print(df)

    # Schritt 2: Daten visualisieren

    # Boxplot erstellen, um die Verteilung der Größen für konventionelle vs. nicht-konventionelle Repos zu vergleichen
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='Konventionell', y='Size', data=df)
    plt.title('Verteilung der Repository-Größen nach Konventionalität')
    plt.xlabel('Konventionell')
    plt.ylabel('Größe')
    plt.show()

    # Alternativ: Scatterplot mit Jitter, um die Datenpunkte besser sichtbar zu machen
    plt.figure(figsize=(10, 6))
    sns.stripplot(x='Konventionell', y='Size', data=df, jitter=True, alpha=0.7)
    plt.title('Repository-Größe nach Konventionalität')
    plt.xlabel('Konventionell')
    plt.ylabel('Größe')
    plt.show()

    # Schritt 3: Statistische Analyse (z.B. Mittelwerte)
    mean_sizes = df.groupby('Konventionell')['Size'].mean().reset_index()
    print(mean_sizes)

    # Schritt 4: Korrelationskoeffizient berechnen: Da 'Konventionell' eine kategoriale Variable ist, kannst du z.B.
    # den Mittelwert vergleichen oder einen t-Test durchführen. Alternativ, kodieren wir 'Konventionell' als binär
    # und berechnen den Punktbiserialen Korrelationskoeffizienten.

    from scipy.stats import pointbiserialr

    # Kodieren: 'Ja' = 1, 'Nein' = 0
    df['Konv_Binary'] = df['Konventionell'].map({'Ja': 1, 'Nein': 0})

    # Berechne den Punktbiserialen Korrelationskoeffizienten
    corr, p_value = pointbiserialr(df['Konv_Binary'], df['Size'])
    print(f"Punktbiserialer Korrelationskoeffizient: {corr:.3f}, p-Wert: {p_value:.3f}")
