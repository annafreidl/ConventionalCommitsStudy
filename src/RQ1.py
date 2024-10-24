from pathlib import Path
from data_saver import load_dataset, load_analysis_summaries
from process_repository import process_repository

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
RESULTS = ROOT / "results" / "commit_messages_test"
YAML = ROOT / "data" / "test.yaml"

# RQ1: Analysing the consistency of CC applications and the distribution and frequency
# of commit types.
#
# – Adoption Rate: To what extent are CC guidelines being followed in different open
# source projects? Are there differences in adoption rates based on factors such as
# programming language, project size, or community activity?

# – Consistency: How consistently are CC guidelines applied within projects that have
# adopted them? Are there discrepancies in usage patterns among individual devel-
# opers within the same project?

# – Commit Type Distribution: What is the frequency distribution of different commit
# types (e.g., bug fixes, feature additions, documentation updates) within projects?
# Are there patterns related to project type, development phase, or team size?

# – Impact on Project Management: How does the distribution of commit types influ-
# ence project management tasks such as effort estimation and resource allocation?
# Is it possible to identify correlations between commit patterns and project outcomes

if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    repos = load_dataset(YAML)

    i = 0

    for repo_data in repos:
        i += 1
        process_repository(repo_data, RESULTS)
        print(f"Processed {i} repos")


#TODO:  1.1 Overall Adoption Rate - Alle Repos
# 1.1.1 Adoption Rate by Programming Language
# 1.1.2 Adoption Rate by Project Size
# 1.1.3 Adoption Rate by Community Activity
# 1.1.4 Adoption Rate by Project Age

#TODO: RQ1.2 Consistency - Wer nutzt CC? - auf CC und Non-CC Repos anwenden
# 1.2.1 Consistency auf Entwicklerebene
# Aufschlüsseln der Contibutor in 4 Gruppen:
# - Core developers
# - Active contributors
# - Occasional contributors
# - One-time contributors
# Verteilung der Contributor-Typen plotten
# Verteilung der Commits nach Contributor-Typen plotten
# Vergleich der Verteilung der Commits nach Contributor-Typen vor und nach der Adoption
# 1.2.2 Consistency über die Zeit - mal schauen

# Ergebnis z.B.
# Nach der Adoption von CC nutzen zu 90% Core Developers CC,
# One-time Contributors nutzen nur in 10% der Fälle CC

#TODO 1.3 Commit Type Distribution - nur auf Repos mit CC anwenden
# 1.3.1 Commit Type Distribution -- CC-Types
# - total
# - by Programming Language
# - by Contributor Type
# 1.3.2 Commit Type Distribution -- Custom-Types
# - total - manuelle Auswertung der ersten ... types
# - by Programming Language
# - by Contributor Type
# 1.3.3 Exkurs: custom-types mit ChatGPT API analysieren und kategorisieren - weiterführende Forschung

#TODO 1.4 Impact on Project Management --> ggf. weiterführende Forschung
# 1.4.1 Effekt auf Effort Estimation
# 1.4.2 Effekt auf Resource Allocation
# 1.4.3 Effekt auf Projektmanagement-Tasks







