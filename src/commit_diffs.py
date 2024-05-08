from tqdm import tqdm
import concurrent.futures


def load_commits(repo):
    return list(repo.iter_commits(all=True))


def calculate_diffs(diffs):
    diff_str = ""
    for diff in diffs:
        if isinstance(diff.diff, bytes):
            diff_text = diff.diff.decode("utf-8")
        else:
            diff_text = diff.diff
        formatted_header = f"diff --git a/{diff.a_path} b/{diff.b_path}\n"
        diff_str += formatted_header + diff_text + "\n"
    return diff_str


def load_diffs(repo, length=None):
    commits = load_commits(repo)
    if length:
        commits = commits[:length]

    diffs = []
    for commit in tqdm(commits, desc="Loading diffs"):
        diff = commit.diff(create_patch=True, R=True)
        diffs.append((commit.hexsha, calculate_diffs(diff)))
    return diffs


def load_diffs_parallel(repo):
    commits = load_commits(repo)
    print(f"Total commits: {len(commits)}")
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        print("start")
        futures = [
            executor.submit(process_commit, commit, idx, len(commits))
            for idx, commit in enumerate(commits)
        ]
        results = [
            future.result() for future in concurrent.futures.as_completed(futures)
        ]
        results.sort(key=lambda x: x[1])
        diffs = [result[0] for result in results]
        diffs_only = [result[2] for result in results]

    return diffs, diffs_only


def process_commit(commit, index, total):
    commit_diffs = {
        "commit": commit,
        "diffs": commit.diff(create_patch=True, R=True),
    }
    diff_str = calculate_diffs(commit.diff(create_patch=True, R=True))
    print(f"commit {index}/{total}")
    return commit_diffs, index, diff_str
