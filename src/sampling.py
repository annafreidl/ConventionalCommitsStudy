import random
import json
from pathlib import Path

from constants import ROOT, SAMPLE_SIZE


def load_custom_type_commits(results_dir):
    """
    Loads all commits classified as 'Conventional Commits with custom types'.

    Args:
        results_dir (Path): Directory containing the analysis results.

    Returns:
        list: List of commits with custom types.
    """
    custom_commits = []
    # Iterate over all repository commit message files
    for repo_file in results_dir.glob("*_commit_messages.json"):
        with open(repo_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            commits = data.get('commits', [])
            for commit in commits:
                if commit.get('is_conventional') and commit.get('custom_type'):
                    custom_commits.append(commit)
    return custom_commits

def sample_commits(commit_list, sample_size):
    """
    Randomly samples commits from the provided list.

    Args:
        commit_list (list): List of commits (e.g., commit hashes).
        sample_size (int): Number of commits to sample.

    Returns:
        list: Randomly sampled commits.
    """
    if len(commit_list) < sample_size:
        print(f"Warning: Population size ({len(commit_list)}) is less than the sample size ({sample_size}). Using entire population.")
        return commit_list
    return random.sample(commit_list, sample_size)

def save_sampled_commits(sampled_commits, output_file):
    """
    Saves the sampled commits to a JSON file.

    Args:
        sampled_commits (list): List of sampled commits.
        output_file (Path): Path to the output JSON file.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sampled_commits, f, indent=2)


if __name__ == "__main__":
    RESULTS_DIR = ROOT / "results" / "commit_messages" # Ersetze durch deinen tatsächlichen Pfad
    classification_file = ROOT / "results" / "repository_classifications.json"
    OUTPUT_DIR = ROOT / "results" / "sample.json"  # Ersetze durch dein gewünschtes Ausgabeverzeichnis

    custom_commits = load_custom_type_commits(RESULTS_DIR)
    print(f"Total commits with custom types: {len(custom_commits)}")

    # Perform random sampling
    sampled_commits = sample_commits(custom_commits, SAMPLE_SIZE)
    print(f"Number of commits sampled: {len(sampled_commits)}")

    # Save sampled commits for manual verification
    save_sampled_commits(sampled_commits, OUTPUT_DIR)
    print(f"Sampled commits saved to {OUTPUT_DIR}")