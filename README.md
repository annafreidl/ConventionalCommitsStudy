# Conventional Commit Analysis

This repository holds the code used to analyze the adoption and impact of the  [Conventional Commits 
Specification (CCS)](www.conventionalcommits.org) across open-source software projects.

The code facilitates data collection, processing, and analysis – all as detailed in the bachelor thesis, "Commit Conventions: Conception and Impact of the Conventional Commit Specification in Open Source."

## Overview
This project investigates the adoption rates and consistency of CCS in open-source repositories and analyzes its effects on commit behaviors. Using data from GitHub, it evaluates how the introduction of CCS affects commit patterns, structure, and documentation quality, providing insights for software development practices and automation.

## Installation
Here's how to get up and running:

1. Clone the repository

```bash
git clone https://github.com/annafreidl/ConventionalCommitsStudy.git
```
2. Install Required Libraries
```bash
pip install -r requirements.txt
```
3. Set GITHUB_TOKEN as an environment variable with a valid GitHub API token.
```bash
export GITHUB_ACCESS_TOKEN=your_token_here
```
**Note:** You'll need a valid GitHub API token for this step.

## Data Structure
The project directory is organized as follows:
```
project_root/
├── data/
├── src/
│   ├── data/
│   │   └── dataset.json (dataset: input data)
│   ├── results/
│   │   ├── commit_messages/ (processed data)
│   │   ├── final_plots/ (results of RQ1 and RQ2)
│   │   ├── error_log.txt (log of errors encountered during cloning)
│   │   ├── overall_results.txt (overall results of RQ1)
│   ├── analyzer.py
│   ├── change_point_detection.py
│   ├── commit_loader.py
│   ├── constants.py
│   ├── data_enricher.py
│   ├── data_saver.py
│   ├── main.py (main script to run the analysis)
│   ├── process_repository.py
│   ├── repository_manager.py
│   ├── RQ1.py
│   └── RQ2.py
```

- **Input Data**: Open-source repositories, sampled based on language and star count.
- **Processed Data**: Metadata and labeled commit data for each repository, stored in JSON format.
Conventional Commits Adoption Analysis in Open-Source Projects
- **Results**: Final plots for each research question, including adoption rates, distribution across languages, and commit behavior changes.


## Dataset

The dataset consists of 2,495 GitHub repositories spanning ten of the most popular programming languages. 
After filtering out inactive, private, or deactivated repositories, the final analysis includes repositories with a 
substantial number of stars and contributors, ensuring high-quality and actively maintained projects.

Here's a breakdown of the programming languages included:

| Language   | Number of Projects | Average Contributors | Average Stars | Average Age in Years |
|------------|--------------------|---------------------|---------------|---------------------|
| Python     | 249                | 428                 | 37620         | 6.5                 |
| JavaScript | 249                | 340                 | 35902         | 9.7                 |
| Go         | 250                | 347                 | 23344         | 8.1                 |
| C++        | 249                | 399                 | 19777         | 9                   |
| Java       | 250                | 256                 | 20310         | 9.1                 |
| TypeScript | 250                | 507                 | 34520         | 7.1                 |
| C          | 249                | 500                 | 13798         | 9.2                 |
| C#         | 249                | 172                 | 9874          | 8.3                 |
| PHP        | 250                | 272                 | 9656          | 10.8                |
| Rust       | 250                | 286                 | 15101         | 5.9                 |
## Research Questions

- **RQ1:** To what extent and with what consistency are Conventional Commits (CC) adopted? 
- **RQ2:** How does the adoption of Conventional Commits influence commit behaviors before and after its adoption?

## Methods

- **Adoption Detection**: Identified CC adoption based on the presence of a valid cc_adoption_date and consistent use of CC in commit messages.
- **Statistical Analysis**: Calculated adoption rates, compared commit metrics before and after adoption, and assessed correlations between CC adoption and repository metrics.
- **Visualization**: Generated bar plots and other visual aids to illustrate adoption rates and their impacts.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
Contact

For any questions or suggestions, please contact:

    Name: Anna Freidl
    Email: annafreidl@yahoo.de
    GitHub: annafreidl

## Acknowledgments

    Conventional Commits Specification: Conventional Commits
    GitHub: For hosting the repositories and providing valuable data for analysis.
    Open-Source Community: For their continuous contributions and collaboration.

