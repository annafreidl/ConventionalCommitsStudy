# analyzer.py

import re
from pathlib import Path
import json

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

    if not using_cc and not adoption_date_exists:
        return "nicht conventional"
    elif not using_cc and adoption_date_exists:
        return "nutzen CC, aber nicht als Vorgabe erkennbar"
    elif using_cc and adoption_date_exists:
        return "nutzen CC und als Vorgabe erkennbar"
    elif using_cc and not adoption_date_exists:
        return "Vorgabe/Erwähnung von CC, aber wird nicht genutzt"
    else:
        return "nicht eindeutig klassifizierbar"

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

    # 4. Durchsicht der Dokumentation
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
    Durchsucht Dokumentationsdateien nach Erwähnungen der Conventional Commit Konvention.

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
        "Commit Message Convention",
        "Commit Guidelines",
        "commitizen",
        "commitlint",
        "standard-version",
        "semantic-release"
    ]

    for doc_file in doc_files:
        doc_path = local_path / doc_file
        if doc_path.exists():
            with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for keyword in keywords:
                    if re.search(r'\b' + re.escape(keyword) + r'\b', content, re.IGNORECASE):
                        print(f"Keyword '{keyword}' gefunden in {doc_file}")
                        return True
    return False
