import re


def _tokenize(text: str) -> set[str]:
    """Lowercase and split text into a set of tokens."""
    return set(re.findall(r"[a-z0-9#+.]+", text.lower()))


def score_job(job: dict, profile: dict) -> int:
    """
    Score a job against a parsed resume profile (0-100).

    Weights:
      - Skills match:     up to 60 points
      - Job title match:  up to 25 points
      - Location match:   up to 15 points
    """
    score = 0.0

    job_text = f"{job['title']} {job['description']}".lower()
    job_tokens = _tokenize(job_text)

    # --- Skills match (60 pts max) ---
    user_skills = [s.lower().strip() for s in profile.get("skills", []) if s]
    if user_skills:
        matched = sum(1 for skill in user_skills if skill in job_text)
        score += (matched / len(user_skills)) * 60

    # --- Title match (25 pts max) ---
    user_titles = [t.lower().strip() for t in profile.get("job_titles", []) if t]
    if user_titles:
        title_tokens = _tokenize(job["title"])
        best_title_score = 0.0
        for title in user_titles:
            title_parts = _tokenize(title)
            if title_parts:
                overlap = len(title_parts & title_tokens) / len(title_parts)
                best_title_score = max(best_title_score, overlap)
        score += best_title_score * 25

    # --- Location match (15 pts max) ---
    user_location = profile.get("location", "").lower().strip()
    job_location = job.get("location", "").lower()
    if user_location and job_location:
        if user_location in job_location or job_location in user_location:
            score += 15
        else:
            loc_parts = _tokenize(user_location)
            job_loc_parts = _tokenize(job_location)
            if loc_parts & job_loc_parts:
                score += 8
        if "remote" in job_location:
            score += 7

    return min(int(round(score)), 100)


def rank_jobs(jobs: list[dict], profile: dict) -> list[dict]:
    """Score all jobs and return sorted by match score descending."""
    for job in jobs:
        job["match_score"] = score_job(job, profile)
    return sorted(jobs, key=lambda j: j["match_score"], reverse=True)
