# commit_loader.py
import re

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
            pretty="%H;%ct;%an;%s",
            shortstat=True
        )

        lines = git_log_output.split('\n')
        current_commit = None

        stats_regex = re.compile(r"(\d+) files? changed(, (\d+) insertions?\(\+\))?(, (\d+) deletions?\(-\))?")

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
                        'deletions': 0,
                        'files_changed': 0
                    }
            elif line.strip() and current_commit:
                match = stats_regex.search(line.strip())
                if match:
                    files_changed = int(match.group(1)) if match.group(1) else 0
                    insertions = int(match.group(3)) if match.group(3) else 0
                    deletions = int(match.group(5)) if match.group(5) else 0
                    current_commit['insertions'] += insertions
                    current_commit['deletions'] += deletions
                    current_commit['files_changed'] += files_changed

                    if current_commit['files_changed'] > 0:
                        commits.append(current_commit)
                    current_commit = None
        return commits
    except GitCommandError as e:
        print(f"Fehler beim Laden der Commits: {e}")
        return []
