# commit_loader.py

from git import GitCommandError
import datetime

def load_commits(repo):
    """
    Lädt Commit-Daten aus einem Repository.

    Args:
        repo (Repo): GitPython Repository Objekt.

    Returns:
        list: Liste von Commit-Daten.
    """
    commits = []
    try:
        default_branch = repo.active_branch.name
    except (TypeError, AttributeError):
        default_branch = "HEAD"

    try:
        git_log_output = repo.git.log(
            default_branch,
            pretty="%H;%ct;%cn;%s",
            shortstat=True
        )

        lines = git_log_output.split('\n')
        current_commit = None
        for line in lines:
            if ';' in line:
                parts = line.strip().split(';')
                if len(parts) >= 4:
                    commit_hash = parts[0]
                    timestamp = int(parts[1])
                    committed_datetime = datetime.datetime.utcfromtimestamp(timestamp).isoformat()
                    author = parts[2]
                    message = parts[3]
                    current_commit = {
                        'committed_datetime': committed_datetime,
                        'message': message.strip(),
                        'author': author.strip(),
                        'insertions': 0,
                        'deletions': 0
                    }
                    commits.append(current_commit)
            elif line.strip() and current_commit:
                parts = line.strip().split('\t')
                if len(parts) == 3:
                    insertions_str, deletions_str, filename = parts
                    insertions = int(insertions_str) if insertions_str.isdigit() else 0
                    deletions = int(deletions_str) if deletions_str.isdigit() else 0
                    current_commit['insertions'] += insertions
                    current_commit['deletions'] += deletions
        return commits
    except GitCommandError as e:
        print(f"Fehler beim Laden der Commits: {e}")
        return []
