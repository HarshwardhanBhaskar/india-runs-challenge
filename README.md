# Redrob Candidate Discovery & Ranking System (Track 1)

This repository contains the candidate ranking submission by **Team HB Technologies** for Track 1 (Data & AI Challenge) of the Redrob Intelligent Candidate Discovery & Ranking Challenge.

## Project Description

The solution is an offline, high-throughput, and deterministic candidate screening pipeline designed to rank a 100,000-candidate pool for a **Senior AI Engineer (Founding Team)** role in **under 50 seconds** on a single CPU core. 

Instead of relying on heavy black-box LLM APIs (which violate latency, offline, and cost constraints), it employs a multi-tier heuristic model matching candidates across five key vectors:
1. **Title Relevance (35%):** Heavy weight on ML/AI engineering experience, with down-weighting for non-tech roles.
2. **Target Skills & Durations (25%):** Captures core IR/RAG and Nice-to-Have skills, accounting for proficiency multipliers and usage duration.
3. **Experience Bracket (20%):** Matches the target 5-9 years of experience bracket.
4. **Company Fit (10%):** Prioritizes product/startup backgrounds, applying a -20% final penalty for candidates with service-firm-only history.
5. **Location & Hireability (10%):** Rewards Noida/Pune availability, high recruiter response rates, and shorter notice periods (<30 days).

### Key Features
* **Honeypot Shield:** Programmatically flags and disqualifies synthetic profiles (e.g., candidates listing "expert" proficiency with 0 months of experience or tenure preceding company founding dates).
* **Deep Parsing:** Utilizes a context-aware regex parser to identify "Tier 5" candidates who built vector databases or retrieval systems but omitted industry buzzwords.
* **Explainable Outputs:** Dynamically generates custom, hallucination-free summaries of qualifications for each of the top 100 candidates based strictly on verified profile facts.

---

## Setup & Requirements

### System Requirements
* Python 3.12+
* No external package dependencies are required (built entirely with Python standard libraries).

---

## How to Run & Reproduce Results

To run the candidate ranker end-to-end and generate the ranked CSV file, run the following command at the root of this repository:

```bash
python rank.py --candidates ./candidates.jsonl --out ./hb_technologies.csv
```

### Command Arguments
* `--candidates`: Path to the input candidate database (`candidates.jsonl` or `candidates.jsonl.gz`).
* `--out`: Path to write the output ranked CSV file.

The resulting output matches the validation requirements exactly, listing the top 100 candidates ranked from best-fit (Rank 1) to 100th-fit (Rank 100).
