## Repository overview:

```
project_root/
├── data/
├── src/
│   ├── data/
│   │   └── dataset.json
│   ├── results/
│   │   ├── commit_messages/
│   │   ├── final_plots/
│   │   ├── error_log.txt
│   │   ├── overall_results.txt
│   ├── analyzer.py
│   ├── change_point_detection.py
│   ├── commit_loader.py
│   ├── constants.py
│   ├── data_enricher.py
│   ├── data_saver.py
│   ├── main.py
│   ├── process_repository.py
│   ├── repository_manager.py
│   ├── RQ1.py
│   └── RQ2.py
```

Conventional Commits Adoption Analysis in Open-Source Projects

Table of Contents

    Introduction
    Objectives
    Dataset
    Data Collection
    Data Analysis
    Results
    Visualizations
    Installation
    Usage
    Contributing
    License
    Contact
    Acknowledgments

Introduction

Conventional Commits (CC) is a specification for adding human and machine-readable meaning to commit messages. By following a structured format, CC enhances the clarity and consistency of commit histories, facilitating better collaboration, automation, and project maintenance. This project investigates the adoption of Conventional Commits within the open-source community, analyzing how widely it is adopted across different programming languages and its impact on commit behaviors.
Objectives

    Assess the Adoption of Conventional Commits: Determine the extent to which open-source projects adopt the Conventional Commits specification.
    Analyze Distribution Across Languages: Examine how CC adoption varies among the top 10 most popular programming languages on GitHub.
    Evaluate Commit Behavior Changes: Investigate how adopting CC influences commit metrics such as insertions, deletions, and commit frequency.
    Understand Documentation vs. Practice: Compare repositories that mention CC in their documentation against actual adoption to identify discrepancies.

Dataset

The dataset consists of 2,495 GitHub repositories spanning ten of the most popular programming languages. After filtering out inactive, private, or deactivated repositories, the final analysis includes repositories with a substantial number of stars and contributors, ensuring high-quality and actively maintained projects.
Programming Languages Included

    Python
    JavaScript
    Go
    C++
    Java
    TypeScript
    C
    C#
    PHP
    Rust

Summary Statistics
Metric	Total	Average	Median
Stars	54,858,400	21,987.3	16,309
Commits	19,403,873	7,777.1	1,939
Contributors	874,722	350.59	149
Size (bytes)	495,196,000	198,476	31,273
Age (years)	-	8.36	8.46
Data Collection
3.2 Data Collection

To ensure a robust dataset, we selected popular open-source projects with a high level of collaboration from GitHub, the most widely used version control system and hosting platform for public repositories. We focused on the top 10 programming languages based on the number of stars received in the first quarter of 2024. For each language, we sampled 250 of the most popular projects based on their GitHub star ratings, resulting in an initial dataset of 2,500 repositories. After excluding deactivated, moved, or private repositories, the final dataset comprises 2,495 unique projects.

Table 1: Summary of Projects by Programming Language
Language	No. of Projects	Avg. Contributors	Avg. Stars	Avg. Age in Years
Python	249	428	37,620	6.5
JavaScript	249	340	35,902	9.7
Go	250	347	23,344	8.1
C++	249	399	19,777	9.0
Java	250	256	20,310	9.1
TypeScript	250	507	34,520	7.1
C	249	500	13,798	9.2
C#	249	172	9,874	8.3
PHP	250	272	9,656	10.8
Rust	250	286	15,101	5.8

Table 1: Summary of Projects by Programming Language
Data Analysis
Research Questions

    RQ1: To what extent and with what consistency are Conventional Commits (CC) adopted?
    RQ2: How does the adoption of Conventional Commits influence commit behaviors before and after its adoption?

Methods

    Adoption Detection: Identified CC adoption based on the presence of a valid cc_adoption_date and consistent use of CC in commit messages.
    Statistical Analysis: Calculated adoption rates, compared commit metrics before and after adoption, and assessed correlations between CC adoption and repository metrics.
    Visualization: Generated bar plots and other visual aids to illustrate adoption rates and their impacts.

Results
4.1 Overview of the Dataset

Our dataset consists of 2,495 repositories with a total of 19,403,873 commits. The repositories cover ten programming languages, with Python, JavaScript, and Go being the most prevalent. The average repository has 350.59 contributors and 21,987 stars, with an average age of 8.36 years.
4.2 RQ1: Extent and Consistency of CC Adoption

Out of the 2,495 repositories analyzed, 334 have adopted Conventional Commits, resulting in an adoption proportion of 13.39%. Among these adopters:

    74 repositories consistently used CC from the beginning.
    260 repositories adopted CC at a later stage.

Bar Chart: Abbildung 1 – CC-Adoptionsstatus der Repositories (Nicht-CC, Konsistent CC, Spätere CC-Adoption)

CC Adoption by Programming Language

CC adoption rates vary significantly across programming languages:

    TypeScript: 48.4%
    Rust: 20.8%
    JavaScript: 19.28%
    Go: 16.8%
    Java: 8.4%
    Python: 5.62%
    C++: 5.22%
    PHP: 5.20%
    C#: 2.41%
    C: 1.61%

Abbildung 2: Balkendiagramm der CC-Adoptionsraten pro Programmiersprache.

CC Indication vs. Actual Adoption

Table 2: Comparison of cc indication and CC Adoption
	CC Adopted	CC Not Adopted	Total
cc indication: True	93	47	140
cc indication: False	241	2,114	2,355
Total	334	2,161	2,495

From the table:

    66.43% of repositories with a cc indication flag have adopted CC.
    33.57% of repositories with a cc indication flag have not adopted CC.
    10.24% of repositories without a cc indication flag have adopted CC.

This indicates that while documentation can be a useful indicator of CC adoption, many projects implement CC without explicitly mentioning it.

Abbildung 3: Balkendiagramm der CC-Adoptionsraten basierend auf cc indication.

Correlations with Repository Metrics

    Size: 0.01 (Negligible)
    Total Commits: -0.03 (Negligible)
    Repository Age: -0.16 (Weak Negative)

The negative correlation with repository age suggests that newer repositories are more likely to adopt CC practices.

Abbildung 4: Streudiagramm der CC-Adoption im Verhältnis zum Repository-Alter.
4.3 RQ2: Influence of CC Adoption on Commit Behaviors

We analyzed commit-level metrics before and after CC adoption for repositories that implemented CC during their development.

Table 3: Commit Metrics Before and After CC Adoption
Metric	Before Adoption	After Adoption
Files Changed (avg)	6.26	7.54
Insertions (avg)	304.12	269.76
Deletions (avg)	221.70	206.48
Total Commits	734,875	980,408

Findings:

    Files Changed: Increased slightly, suggesting more comprehensive commits.
    Insertions & Deletions: Decreased, indicating more granular and focused commits.
    Total Commits: Increased, reflecting more frequent committing practices.

Abbildung 5: Gruppiertes Balkendiagramm der durchschnittlichen Einfügungen und Löschungen pro Commit vor und nach CC-Adoption.

Statistical Significance

Statistical tests confirmed that the changes in insertions, deletions, and total commits are significant (p < 0.05).
Summary

Adopting Conventional Commits is associated with more granular commits and increased commit frequency, enhancing project maintainability and collaboration.
Visualizations

The project includes several visualizations to illustrate the findings:

    Figure 1: CC-Adoptionsstatus der Repositories (Balkendiagramm)
    Figure 2: CC-Adoptionsraten pro Programmiersprache (Balkendiagramm)
    Figure 3: CC-Indikation vs. tatsächliche Adoption (Balkendiagramm)
    Figure 4: Korrelation zwischen CC-Adoption und Repository-Alter (Streudiagramm)
    Figure 5: Einfluss der CC-Adoption auf Commit-Metriken (Gruppiertes Balkendiagramm)

All visualizations can be found in the plots/ directory.
Installation
Prerequisites

    Python 3.8 or higher
    Git

Clone the Repository

git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name

Create a Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install Dependencies

pip install -r requirements.txt

requirements.txt should include all necessary Python packages, such as:

pandas
numpy
matplotlib
seaborn
python-dateutil

Usage
Data Collection

Ensure you have access to the GitHub API and necessary permissions. Update the data collection script with your GitHub credentials if required.

python data_collection.py

Data Analysis

Run the analysis scripts to process the collected data.

python data_analysis.py

Generating Visualizations

Use the provided plotting functions to generate and save visualizations.

python plot_scripts.py

For example, to plot the adoption rate by project type:

from plot_scripts import plot_adoption_rate_by_project_type

adoption_rates = {
    'Organization': 15.7,
    'User': 8.3
}
file_path = 'plots/adoption_rate_by_project_type.png'

plot_adoption_rate_by_project_type(adoption_rates, file_path)

Contributing

Contributions are welcome! Please follow these steps:

    Fork the Repository
    Create a New Branch

git checkout -b feature/YourFeature

    Commit Your Changes

git commit -m "Add your message here"

    Push to the Branch

git push origin feature/YourFeature

    Open a Pull Request

License

This project is licensed under the MIT License. See the LICENSE file for details.
Contact

For any questions or suggestions, please contact:

    Name: Your Name
    Email: your.email@example.com
    GitHub: yourusername

Acknowledgments

    Conventional Commits Specification: Conventional Commits
    GitHub: For hosting the repositories and providing valuable data for analysis.
    Open-Source Community: For their continuous contributions and collaboration.

This README was generated to provide a comprehensive overview of the Conventional Commits Adoption Analysis project, outlining its objectives, methodology, results, and usage instructions