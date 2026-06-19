import json
import csv
import re
import argparse
import sys
from pathlib import Path

# Regex to detect years in descriptions
YEAR_PATTERN = re.compile(r'\b(19\d{2}|20\d{2})\b')
# Keywords that suggest company establishment
ESTABLISH_KEYWORDS = ["found", "establish", "start", "launch", "incorporat", "incept", "setup", "set up", "began", "begin", "origin", "create"]

def is_honeypot(cand):
    # Check 1: Expert proficiency with 0 duration (for any skill)
    for s in cand.get("skills", []):
        if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0:
            return True
            
    # Check 2: Company establishment year mismatch
    for exp in cand.get("career_history", []):
        desc = exp.get("description", "")
        start_date = exp.get("start_date")
        if not start_date or not desc:
            continue
        
        start_year = int(start_date[:4])
        years_in_desc = [int(y) for y in YEAR_PATTERN.findall(desc)]
        
        for y in years_in_desc:
            if start_year < y:
                pos = desc.find(str(y))
                context = desc[max(0, pos-40):min(len(desc), pos+40)].lower()
                if any(kw in context for kw in ESTABLISH_KEYWORDS):
                    return True
                    
    return False

def evaluate_candidate(cand):
    # 0. Disqualify honeypots
    if is_honeypot(cand):
        return -1.0, "Disqualified: Profile contains impossible or inconsistent information."
        
    profile = cand["profile"]
    skills = cand["skills"]
    history = cand["career_history"]
    education = cand["education"]
    signals = cand["redrob_signals"]
    
    # 1. Experience Score (Max: 20 points)
    # Target: 5-9 years (6-8 is perfect).
    yoe = profile.get("years_of_experience", 0.0)
    exp_score = 0.0
    if 5.0 <= yoe <= 9.0:
        exp_score = 20.0
    elif 4.0 <= yoe < 5.0:
        exp_score = 15.0
    elif 9.0 < yoe <= 12.0:
        exp_score = 15.0
    elif 12.0 < yoe <= 15.0:
        exp_score = 10.0
    elif 3.0 <= yoe < 4.0:
        exp_score = 5.0
    else:
        exp_score = 0.0
        
    # 2. Title & Role Relevance Score (Max: 35 points)
    current_title = profile.get("current_title", "").lower()
    headline = profile.get("headline", "").lower()
    
    # Check if they are in a non-tech role (immediate down-weight)
    non_tech_keywords = ["marketing", "accountant", "hr manager", "human resources", "sales", "civil engineer", "mechanical engineer", "customer support", "operations manager"]
    is_non_tech = any(kw in current_title or kw in headline for kw in non_tech_keywords)
    
    # Keywords matching Senior AI/ML roles
    ai_title_keywords = ["ai engineer", "ml engineer", "machine learning", "data scientist", "nlp", "founding engineer"]
    is_ai_role = any(kw in current_title or kw in headline for kw in ai_title_keywords)
    is_senior = any(kw in current_title or kw in headline for kw in ["senior", "lead", "principal", "founding"])
    
    title_score = 0.0
    if is_non_tech:
        title_score = -10.0
    elif is_ai_role:
        if is_senior:
            title_score = 35.0
        else:
            title_score = 28.0
    elif "backend" in current_title or "software engineer" in current_title or "full stack" in current_title:
        title_score = 15.0
    else:
        title_score = 5.0
        
    # 3. Skills Score (Max: 25 points)
    core_skills = {
        "embeddings", "sentence transformers", "bge", "e5", "openai embeddings", 
        "vector database", "vector databases", "pinecone", "weaviate", "qdrant", "milvus", 
        "elasticsearch", "opensearch", "faiss", "hybrid search", "retrieval", "semantic search",
        "rag", "nlp", "information retrieval", "evaluation", "ndcg", "map", "mrr"
    }
    nice_to_haves = {
        "lora", "qlora", "peft", "llm fine-tuning", "fine-tuning", "learning to rank", 
        "xgboost", "distributed systems", "large-scale inference", "mlops", "mlflow"
    }
    
    skills_score = 0.0
    matched_skills = []
    
    for s in skills:
        s_name = s["name"].lower()
        prof = s.get("proficiency", "beginner")
        dur = s.get("duration_months", 0)
        
        prof_mult = {"expert": 4.0, "advanced": 3.0, "intermediate": 2.0, "beginner": 1.0}.get(prof, 1.0)
        
        if s_name in core_skills:
            skills_score += prof_mult * min(dur / 12.0, 3.0)  # cap at 3 years
            matched_skills.append(s["name"])
        elif s_name in nice_to_haves:
            skills_score += 0.5 * prof_mult * min(dur / 12.0, 3.0)
            matched_skills.append(s["name"])
            
    # Check career description for plain-language Tier 5 skills (crucial for candidates who built things but didn't list buzzwords)
    desc_points = 0.0
    desc_skills_matched = []
    history_desc_combined = " ".join([h.get("description", "").lower() for h in history])
    
    desc_keywords = {
        "RAG": ["rag", "retrieval-augmented generation", "retrieval augmented"],
        "Vector Search": ["vector search", "dense retrieval", "semantic search", "embeddings-based retrieval"],
        "Vector Databases": ["pinecone", "weaviate", "qdrant", "milvus", "faiss", "opensearch", "elasticsearch"],
        "Eval Metrics": ["ndcg", "mrr", "map score", "evaluation framework", "ranking system", "re-ranking", "rerank"],
        "Fine-Tuning": ["fine-tuning", "lora", "qlora", "peft", "fine tune"]
    }
    
    for skill_cat, kw_list in desc_keywords.items():
        if any(kw in history_desc_combined for kw in kw_list):
            desc_points += 2.0
            desc_skills_matched.append(skill_cat)
            
    skills_score = min(25.0, skills_score + desc_points)
    
    # 4. Service vs Product Company Score (Max: 10 points)
    service_companies = {"tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini"}
    all_companies = [h.get("company", "").lower() for h in history if h.get("company")]
    
    is_service_only = len(all_companies) > 0 and all(c in service_companies for c in all_companies)
    has_product_exp = any(c not in service_companies for c in all_companies)
    
    company_score = 0.0
    if is_service_only:
        company_score = 0.0
    elif has_product_exp:
        company_score = 10.0
    else:
        company_score = 5.0
        
    # 5. Location & Relocation Score (Max: 5 points)
    loc = profile.get("location", "").lower()
    willing_reloc = signals.get("willing_to_relocate", False)
    
    loc_score = 0.0
    target_cities = ["pune", "noida", "delhi", "gurgaon", "ncr", "mumbai", "hyderabad", "bangalore"]
    in_target_city = any(city in loc for city in target_cities)
    
    if in_target_city:
        loc_score = 5.0
    elif willing_reloc:
        loc_score = 3.0
    else:
        loc_score = 0.0
        
    # 6. Behavioral Signals & Notice Period (Max: 10 points)
    last_active = signals.get("last_active_date", "")
    active_score = 0.0
    if last_active.startswith("2026"):
        active_score = 3.0
    elif last_active.startswith("2025"):
        active_score = 2.0
    elif last_active.startswith("2024"):
        active_score = 0.5
        
    resp_rate = signals.get("recruiter_response_rate", 0.0)
    resp_score = resp_rate * 3.0
    
    otw_score = 2.0 if signals.get("open_to_work_flag", False) else 0.0
    
    notice_days = signals.get("notice_period_days", 180)
    notice_score = 0.0
    if notice_days <= 30:
        notice_score = 2.0
    elif notice_days <= 60:
        notice_score = 1.0
    elif notice_days <= 90:
        notice_score = 0.0
    else:
        notice_score = -2.0
        
    behavioral_score = max(0.0, min(10.0, active_score + resp_score + otw_score + notice_score))
    
    # 7. Additional adjustments & safety checks
    # Penalize candidates who have salary_min > salary_max or education_experience mismatch
    # (even if not full honeypots, we want to down-weight inconsistent profiles)
    salary_range = signals.get("expected_salary_range_inr_lpa", {})
    if salary_range.get("min", 0.0) > salary_range.get("max", 0.0):
        behavioral_score -= 2.0
        
    grad_years = [edu.get("end_year") for edu in education if edu.get("end_year")]
    if grad_years:
        min_grad = min(grad_years)
        career_span = 2026 - min_grad
        if yoe > career_span + 2:
            behavioral_score -= 2.0
            
    behavioral_score = max(0.0, behavioral_score)
    
    # Compute base composite score (out of 100)
    base_score = exp_score + title_score + skills_score + company_score + loc_score + behavioral_score
    
    # Normalise score to range [0.0, 1.0]
    final_score = max(0.0, min(1.0, base_score / 100.0))
    
    # Apply penalty for service only
    if is_service_only:
        final_score = max(0.0, final_score - 0.20)
        
    # Compile reasoning (1-2 sentences)
    reason_parts = []
    
    # Current role & experience
    reason_parts.append(f"{profile.get('current_title', 'Engineer')} with {yoe} years of experience.")
    
    # Skills match
    all_matched = sorted(list(set(matched_skills + desc_skills_matched)))
    if all_matched:
        reason_parts.append(f"Strong background in {', '.join(all_matched[:3])}.")
    
    # Location/availability
    loc_name = profile.get("location", "India")
    if in_target_city:
        reason_parts.append(f"Located in {loc_name} with a {notice_days}-day notice period.")
    else:
        if willing_reloc:
            reason_parts.append(f"Willing to relocate (currently {loc_name}) with a {notice_days}-day notice period.")
        else:
            reason_parts.append(f"Based in {loc_name} ({notice_days}-day notice period).")
            
    reasoning = " ".join(reason_parts)
    
    return final_score, reasoning

def main():
    parser = argparse.ArgumentParser(description="Rank candidates for Senior AI Engineer JD.")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl or candidates.jsonl.gz")
    parser.add_argument("--out", required=True, help="Path to write the ranked CSV file")
    args = parser.parse_args()
    
    cand_path = Path(args.candidates)
    if not cand_path.exists():
        print(f"Error: Candidates file {cand_path} does not exist.")
        sys.exit(1)
        
    print(f"Reading candidates from {cand_path}...")
    
    # Open candidates file (handles gzip if needed)
    if cand_path.suffix == ".gz":
        import gzip
        f = gzip.open(cand_path, "rt", encoding="utf-8")
    else:
        f = open(cand_path, "r", encoding="utf-8")
        
    candidate_scores = []
    
    for idx, line in enumerate(f):
        if not line.strip():
            continue
        try:
            cand = json.loads(line)
        except Exception as e:
            print(f"Warning: Failed to parse line {idx}: {e}")
            continue
            
        cid = cand.get("candidate_id")
        if not cid:
            continue
            
        score, reasoning = evaluate_candidate(cand)
        
        # We store candidate_id, score, reasoning
        # (We will sort later and then assign ranks 1 to 100)
        if score >= 0.0:  # Exclude disqualified honeypots
            candidate_scores.append({
                "candidate_id": cid,
                "score": score,
                "reasoning": reasoning
            })
            
    f.close()
    
    print(f"Scanned {idx+1} candidates. Valid candidates: {len(candidate_scores)}.")
    
    # Sort candidates:
    # 1. By rounded score (4 decimal places) descending
    # 2. Tie-break: by candidate_id ascending
    candidate_scores.sort(key=lambda x: (-round(x["score"], 4), x["candidate_id"]))
    
    # Take top 100 candidates
    top_100 = candidate_scores[:100]
    
    # Write to CSV
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Writing top 100 candidates to {out_path}...")
    with open(out_path, "w", encoding="utf-8", newline="") as csv_f:
        writer = csv.writer(csv_f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        
        for idx, item in enumerate(top_100):
            rank = idx + 1
            # Format score to 4 decimal places
            score_formatted = f"{round(item['score'], 4):.4f}"
            writer.writerow([item["candidate_id"], rank, score_formatted, item["reasoning"]])
            
    print("Ranking and CSV generation complete.")

if __name__ == "__main__":
    main()
