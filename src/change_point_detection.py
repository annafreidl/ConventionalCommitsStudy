# Standard library imports
import logging

# Third-party library imports
import matplotlib.pyplot as plt
import numpy as np
import ruptures as rpt
import seaborn as sns
from matplotlib.colors import ListedColormap

# Local module imports
from constants import MIN_CC_RATE, MIN_COMMITS_AFTER_CP, PLOTS


def plot_heatmap(sequence, change_point_index, adoption_date, repo_name):
    """
    Generates and saves a heatmap to visualize Conventional Commits adoption over time.
    """
    # 1. Prepare data for the heatmap
    heatmap_data = np.array(sequence).reshape(-1, 1)
    sequence_size = len(sequence)
    custom_cmap = ListedColormap(['#ffffff', '#121212'])

    # 2. Plot the heatmap
    plt.figure(figsize=(6.202, 3.500))
    sns.heatmap(heatmap_data.T, cmap=custom_cmap, cbar=False, linecolor='black')

    # 3. Mark the change point
    plt.axvline(x=change_point_index, color='red', linestyle='-', linewidth=2, label='Change Point')

    # 4. Annotate the change point with the adoption date
    plt.annotate(
        f'Adoption Date\n{adoption_date}',
        xy=(change_point_index, 0),
        xytext=(change_point_index + sequence_size * 0.03, 0.6),
        fontsize=10,
        color='black',
        bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='black')
    )

    # 5. Save and format the plot
    save_path = f"{PLOTS}/{repo_name}_heatmap.pdf"
    # plt.title('Conventional Commits Adoption Heatmap', fontsize=14, pad=20)
    # plt.xlabel('Commit Index', fontsize=12)
    # plt.ylabel('CC Compliance', fontsize=12)
    plt.yticks([0, 1], ['CC', 'Non-CC'])
    plt.savefig(save_path)
    plt.close()


def is_repository_conventional_after_cp(commit_sequence_after_cp):
    """
    Determines if a repository consistently uses Conventional Commits after a change point.
    """
    # Calculate the total number of commits after the change point
    total_commits_after_cp = len(commit_sequence_after_cp)
    count_cc = sum(commit_sequence_after_cp)

    # Check if there are enough commits after the change point
    if total_commits_after_cp < MIN_COMMITS_AFTER_CP:
        return False

    # Calculate the CC rate after the change point and check if it meets the minimum rate
    cc_rate_after_cp = count_cc / total_commits_after_cp
    return cc_rate_after_cp >= MIN_CC_RATE


def binary_segmentation_date_analysis(enriched_commits):
    """
    Performs binary segmentation on a commit sequence to detect the date of Conventional Commits adoption.
    """
    adoption_date = None
    commits_reversed = enriched_commits[::-1]

    if len(commits_reversed) == 0:
        return adoption_date

    # Create a binary sequence from the commits (1 = CC, 0 = Non-CC)
    commit_sequence = [1 if commit.get("cc_type") else 0 for commit in commits_reversed]
    length = sum(commit_sequence)

    signal = np.array(commit_sequence)

    # Configure the binary segmentation model with an l2 cost function
    model = "l2"
    algo = rpt.Binseg(model=model).fit(signal)
    change_points = algo.predict(n_bkps=1)  # 'n_bkps' = expected number of change points

    logging.info(f"Found change points: {change_points}")

    # Determine the change point index and evaluate CC consistency after it
    if len(change_points) > 1 and length != 0:
        change_point_index = change_points[0]
        commit_sequence_after_cp = commit_sequence[change_point_index:]
        if is_repository_conventional_after_cp(commit_sequence_after_cp):
            change_point_commit = commits_reversed[change_point_index]
            adoption_date = change_point_commit.get('committed_datetime')[:10]
            # Debugging:plot_heatmap(commit_sequence, change_point_index, adoption_date, 'AUTOGPT')
            logging.info(f"CC usage became consistent from {adoption_date}.")
            return adoption_date
        else:
            return adoption_date
    else:
        print("No significant change point found.")
        return adoption_date
