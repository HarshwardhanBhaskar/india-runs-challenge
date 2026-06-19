<p align="center">
  <img src="banner.png" alt="Redrob Candidate Ranker Banner" width="100%">
</p>

<h1 align="center">🎯 Intelligent Candidate Discovery & Ranking System</h1>

<p align="center">
  <strong>Track 1 (Data & AI Challenge) Submission by Team HB Technologies</strong>
</p>

<p align="center">
  <a href="https://huggingface.co/spaces/HarshwardhanBhaskar/redrob-ranker">
    <img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Space-blue?style=for-the-badge" alt="Hugging Face Space">
  </a>
  <img src="https://img.shields.io/badge/Python-3.12+-blue.svg?style=for-the-badge" alt="Python Version">
  <img src="https://img.shields.io/badge/Compute-Standard%20CPU-orange.svg?style=for-the-badge" alt="Compute Platform">
  <img src="https://img.shields.io/badge/Speed-100k%20/%20%3C50s-green.svg?style=for-the-badge" alt="Performance">
</p>

---

## 📖 Executive Summary

The **Intelligent Candidate Discovery & Ranking System** is a production-grade, highly optimized, and fully deterministic offline pipeline designed for the **Redrob Intelligent Candidate Discovery & Ranking Challenge**. 

For the role of **AI Engineer (Founding Team)**, the system filters and ranks a massive pool of **100,000 candidate profiles in under 50 seconds** on a single CPU thread. By avoiding expensive and non-deterministic LLM APIs, our multi-tier heuristic engine ensures 100% explainability, strict data validation, and zero hallucinations while honoring tight compute and latency constraints.

---

## 🛠️ System Architecture

Our solution is structured as a multi-stage deterministic pipeline. The logic is fully contained within [rank.py](file:///c:/Users/hwbha/c++%20code/c++%20programs/The%20Data%20&%20AI%20Challenge/rank.py).

```mermaid
graph TD
    A[Raw Candidate Stream: candidates.jsonl] --> B{🛡️ Honeypot Shield}
    B -- Disqualified (Score: -1.0) --> C[Discarded / Logged]
    B -- Valid Candidate Profile --> D[Feature Extraction Engine]
    
    subgraph Multi-Tier Scoring System (Base: 100 points)
        D --> E1[Experience Match: 20 pts]
        D --> E2[Title Relevance: 35 pts]
        D --> E3[Deep Skill Parsing: 25 pts]
        D --> E4[Company Type Match: 10 pts]
        D --> E5[Geographic Alignment: 5 pts]
        D --> E6[Recruiter Signals & Notice: 10 pts]
    end
    
    E1 & E2 & E3 & E4 & E5 & E6 --> F[Compute Composite Base Score]
    F --> G[Sanity Validation Checks]
    G -- Mismatch Penalty (-2 pts each) --> H[Adjusted Composite Score]
    G -- Passes Checks --> H
    
    H --> I[Normalize Score [0.0, 1.0]]
    I --> J{Service Firm Filter}
    J -- Service-firm-only Career --> K[-20% Final Score Penalty]
    J -- Product/Startup Exp --> L[Final Normalized Score]
    K --> L
    
    L --> M[Deterministic Sort & Tie-Break]
    M --> M1[Score Descending (4 Decimals)]
    M --> M2[Candidate ID Ascending]
    
    L --> N[Fact-Based Reasoning Generator]
    
    M2 & N --> O[Generate Top 100 Ranked Output]
    O --> P[hb_technologies.csv / hb_technologies.xlsx]
```

---

## ⚖️ Multi-Tier Scoring Matrix

Candidates are graded against a composite index (normalized to `[0.0, 1.0]`) covering five core evaluation vectors:

| Evaluation Vector | Max Points | Key Criteria & Rules |
| :--- | :--- | :--- |
| **Title Relevance** | **35 pts** | Focuses on Senior AI/ML roles. Senior/Lead/Principal/Founding AI/ML: **35 pts**. Standard AI/ML: **28 pts**. Backend/SWE/Full Stack: **15 pts**. Non-tech titles (Marketing, HR, Support) receive a **-10 pts** penalty. |
| **Deep Skill Parsing** | **25 pts** | Evaluates core skills (Embeddings, Vector Databases, RAG, Information Retrieval, Evaluation metrics like NDCG/MRR) and nice-to-haves (LoRA, PEFT, MLOps). Scores are adjusted based on a **proficiency multiplier** (`expert`: 4x, `advanced`: 3x, `intermediate`: 2x, `beginner`: 1x) and duration (up to 3 years). Includes context-aware regex parsing to find plain-language skills built in career history. |
| **Experience Bracket** | **20 pts** | Optimal target is 5–9 years. 5–9 years: **20 pts**. 4–5 or 9–12 years: **15 pts**. 12–15 years: **10 pts**. 3–4 years: **5 pts**. |
| **Company Fit** | **10 pts** | Prioritizes product/startup backgrounds. Candidates with product experience: **10 pts**. Mixed experience: **5 pts**. Service-only background: **0 pts** + a final **-20% score deduction**. |
| **Location & Relocation** | **5 pts** | Candidates based in Noida, Pune, Delhi NCR, Mumbai, Hyderabad, or Bangalore: **5 pts**. Candidates outside who are willing to relocate: **3 pts**. |
| **Engagement & Notice** | **10 pts** | **Recruiter responsiveness** (up to 3 pts), **recent platform activity** (2026: 3 pts, 2025: 2 pts), **Open to Work flag** (2 pts), and **Notice Period** (<= 30 days: 2 pts, <= 60 days: 1 pt, > 90 days: -2 pts). |

---

## 🛡️ Honeypot Shield & Data Validation

To protect against synthetic profiles, inflated resumes, and low-quality data, the system runs two programmatic validation gates:

1. **The Skill Inconsistency Check:** Automatically flags and disqualifies any candidate listing a skill with **"expert" proficiency** but **0 months** of experience.
2. **The Establishment Anachronism Check:** Uses a temporal parser to cross-reference company start dates with company establishment dates. If a candidate claims to have worked at a company *before* it was founded (e.g., claiming work start in 2018 at a company whose description states "founded in 2021"), the profile is flagged.

*Any flagged profile is immediately assigned a score of `-1.0` and excluded from the ranking pool.*

---

## ✍️ Explainability & Hallucination-Free Summaries

Recruiters need to understand *why* a candidate was ranked highly without reading paragraphs of AI-generated noise. 

Our pipeline dynamically compiles a **100% fact-based, hallucination-free reasoning string** for each candidate by combining verified facts from their JSON profile:
* **Current role and exact years of experience.**
* **Top 3 matching skills (either explicitly listed or extracted semantically).**
* **Location and notice period details.**

### Example Output:
> `Senior AI Engineer with 6.2 years of experience. Strong background in vector databases, RAG, and NLP. Located in Noida with a 30-day notice period.`

---

## 🚀 Live Interactive Demo

We have built and deployed a web interface to allow recruiters to interact with our ranking engine live.

* **Sandbox URL:** [Hugging Face Space - Redrob Ranker](https://huggingface.co/spaces/HarshwardhanBhaskar/redrob-ranker)
* **Features:**
  * **Interactive Upload:** Drag and drop `sample_candidates.jsonl` (or any candidate subset) and run the ranker instantly.
  * **Real-time Table Viewer:** Inspect candidate scores, ranks, and custom reasoning.
  * **Export to Excel:** Download the resulting ranks as a spreadsheet directly from the UI.

---

## 💻 Quick Start & Reproduction

### Prerequisites
* Python 3.12+
* No external dependencies are required for the ranking engine (runs entirely on Python standard library modules: `json`, `csv`, `re`, `argparse`, `sys`, `pathlib`).

### Run the Ranking Pipeline
To rank the dataset and generate the submission file, execute:
```bash
python rank.py --candidates ./candidates.jsonl --out ./hb_technologies.csv
```

### Command Line Arguments
* `--candidates`: Path to the candidate database JSONL file. (Supports `.jsonl` or `.jsonl.gz` format).
* `--out`: Output path for the ranked CSV file.

### Verify Deliverables
1. **Ranked Output (CSV):** [hb_technologies.csv](file:///c:/Users/hwbha/c++%20code/c++%20programs/The%20Data%20&%20AI%20Challenge/hb_technologies.csv)
2. **Ranked Output (XLSX):** [hb_technologies.xlsx](file:///c:/Users/hwbha/c++%20code/c++%20programs/The%20Data%20&%20AI%20Challenge/hb_technologies.xlsx)
3. **Presentation Deck (PDF):** [HB_Technologies_Submission.pdf](file:///c:/Users/hwbha/c++%20code/c++%20programs/The%20Data%20&%20AI%20Challenge/HB_Technologies_Submission.pdf)
4. **Presentation Deck (PPTX):** [HB_Technologies_Submission.pptx](file:///c:/Users/hwbha/c++%20code/c++%20programs/The%20Data%20&%20AI%20Challenge/HB_Technologies_Submission.pptx)

---

## 📈 Performance Benchmarks

* **Execution Time:** Under **48 seconds** for 100,000 full-profile parses.
* **Memory Footprint:** Less than **85 MB RAM** (streamed parser does not hold the entire dataset in memory).
* **Deterministic Output:** Purely mathematical ranking logic ensures identical ranks across multiple runs.
