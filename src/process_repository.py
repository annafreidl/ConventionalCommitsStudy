from repository_manager import clone_repository, delete_temp
from commit_loader import load_commits
from data_enricher import enrich_commits
from data_saver import save_to_json, load_from_json
from analyzer import classify_repository
from analyzer import search_for_cc_indications


def process_repository(repo_data, RESULTS_DIR):
    repo_name = repo_data["name"].replace("/", "_")
    json_file_path = RESULTS_DIR / f"{repo_name}_commit_messages.json"

    # Versuche, das Repository zu laden oder zu klonen
    repo = clone_repository(repo_data)
    if repo is None:
        return

    if json_file_path.exists():
        print(f"JSON-Datei für {repo_name} bereits vorhanden.")
        data = load_from_json(json_file_path)
    else:
        # Lade die Commits und reiche sie an
        commits = load_commits(repo)
        enriched_commits, summary = enrich_commits(commits)
        save_to_json(enriched_commits, summary, repo_name, RESULTS_DIR)
        data = {"commits": enriched_commits, "analysis_summary": summary}

    analysis_summary = data.get("analysis_summary", {})
    cc_adoption_date = analysis_summary.get("cc_adoption_date")
    if cc_adoption_date:
        print(f"CC-Einführungsdatum für {repo_name}: {cc_adoption_date}")
    else:
        print(f"Keine CC-Einführung in {repo_name} festgestellt.")

    using_cc = search_for_cc_indications(repo)
    print(f"Repository {repo_name} verwendet Conventional Commits: {using_cc}")

    classification = classify_repository(analysis_summary, using_cc)
    print(f"Das Repository {repo_name} wird klassifiziert als: {classification}")

