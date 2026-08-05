import re
from typing import Dict, List, Any, Optional, Tuple


SKILL_CATEGORIES = {
    "languages": {
        "java": {"level": "expert", "related": ["kotlin", "scala"]},
        "python": {"level": "expert", "related": ["cython"]},
        "javascript": {"level": "expert", "related": ["typescript"]},
        "typescript": {"level": "expert", "related": ["javascript"]},
        "go": {"level": "expert", "related": ["rust"]},
        "rust": {"level": "expert", "related": ["go"]},
        "ruby": {"level": "expert", "related": []},
        "php": {"level": "expert", "related": []},
        "swift": {"level": "expert", "related": ["kotlin"]},
        "kotlin": {"level": "expert", "related": ["java", "swift"]},
    },
    "frameworks": {
        "spring": {"level": "framework", "related": ["spring boot", "hibernate"]},
        "spring boot": {"level": "framework", "related": ["spring", "microservices"]},
        "react": {"level": "framework", "related": ["next.js", "vue"]},
        "vue": {"level": "framework", "related": ["react", "angular"]},
        "angular": {"level": "framework", "related": ["react", "vue"]},
        "django": {"level": "framework", "related": ["fastapi", "flask"]},
        "fastapi": {"level": "framework", "related": ["django", "flask"]},
        "flask": {"level": "framework", "related": ["django", "fastapi"]},
        "nodejs": {"level": "framework", "related": ["express"]},
        "express": {"level": "framework", "related": ["nodejs"]},
    },
    "infrastructure": {
        "aws": {"level": "cloud", "related": ["gcp", "azure"]},
        "gcp": {"level": "cloud", "related": ["aws", "azure"]},
        "azure": {"level": "cloud", "related": ["aws", "gcp"]},
        "docker": {"level": "devops", "related": ["kubernetes"]},
        "kubernetes": {"level": "devops", "related": ["docker", "helm"]},
        "kafka": {"level": "messaging", "related": ["rabbitmq", "redis"]},
        "redis": {"level": "database", "related": ["memcached"]},
        "postgresql": {"level": "database", "related": ["mysql"]},
        "mysql": {"level": "database", "related": ["postgresql"]},
        "mongodb": {"level": "database", "related": []},
    },
    "domains": {
        "microservices": {"level": "architecture", "related": ["distributed systems"]},
        "ai": {"level": "domain", "related": ["machine learning", "llm"]},
        "machine learning": {"level": "domain", "related": ["ai", "data science"]},
        "llm": {"level": "domain", "related": ["ai", "openai"]},
        "devops": {"level": "domain", "related": ["sre", "platform engineering"]},
        "data engineering": {"level": "domain", "related": ["data science"]},
    }
}


LEARNING_TIME_HOURS = {
    "java": 200, "python": 150, "javascript": 180, "typescript": 120,
    "go": 160, "rust": 200, "ruby": 140, "php": 100, "swift": 180, "kotlin": 120,
    "spring": 80, "spring boot": 60, "react": 100, "vue": 80, "angular": 100,
    "django": 60, "fastapi": 40, "flask": 30, "nodejs": 60, "express": 30,
    "aws": 120, "gcp": 120, "azure": 120, "docker": 40, "kubernetes": 80,
    "kafka": 60, "redis": 20, "postgresql": 40, "mysql": 30, "mongodb": 30,
    "microservices": 80, "ai": 200, "machine learning": 300, "llm": 100,
    "devops": 150, "data engineering": 200,
}


def _extract_skills_from_text(text: str) -> List[str]:
    """Extract known skills from free text."""
    if not text:
        return []
    
    text_lower = text.lower()
    found = []
    
    for category in SKILL_CATEGORIES.values():
        for skill in category:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found.append(skill)
    
    return list(set(found))


def _calculate_technical_fit(
    user_skills: List[str],
    job_text: str,
    job_title: str
) -> Tuple[int, List[str], List[str]]:
    """
    Calculate technical fit score (0-100).
    Returns (score, matched_skills, missing_skills).
    """
    if not user_skills:
        return 50, [], []
    
    job_skills = _extract_skills_from_text(f"{job_title} {job_text}")
    
    if not job_skills:
        return 70, [], []
    
    matched = []
    missing = []
    
    for skill in job_skills:
        skill_lower = skill.lower()
        user_has = any(s.lower() == skill_lower for s in user_skills)
        
        if user_has:
            matched.append(skill)
        else:
            missing.append(skill)
    
    if not job_skills:
        return 70, matched, missing
    
    match_ratio = len(matched) / len(job_skills)
    score = int(40 + (match_ratio * 60))
    
    return min(100, max(0, score)), matched, missing


def _calculate_salary_match(
    job_min: Optional[float],
    job_max: Optional[float],
    prefs: Dict
) -> Tuple[int, str]:
    """
    Calculate salary match score (0-100).
    Returns (score, explanation).
    """
    if not job_min and not job_max:
        return 60, "Salary not listed"
    
    if not prefs:
        prefs = {}
    
    desired_min = prefs.get("salary_min") if isinstance(prefs, dict) else None
    desired_max = prefs.get("salary_max") if isinstance(prefs, dict) else None
    
    if not desired_min and not desired_max:
        return 80, "No salary preference set"
    
    job_mid = ((job_min or 0) + (job_max or 0)) / 2 if job_min or job_max else 0
    
    if desired_min and job_mid:
        if job_mid >= desired_min:
            score = min(100, int(80 + ((job_mid - desired_min) / desired_min) * 20))
            return score, f"Matches your ${desired_min:,.0f}+ target"
        else:
            ratio = job_mid / desired_min
            score = int(ratio * 70)
            return max(0, score), f"Below your ${desired_min:,.0f} target"
    
    return 70, "Salary within range"


def _calculate_career_growth(
    job_title: str,
    job_text: str,
    user_seniority: str
) -> Tuple[int, str]:
    """
    Calculate career growth potential (0-100).
    Returns (score, explanation).
    """
    growth_signals = [
        "lead", "staff", "principal", "architect", "director",
        "head of", "vp", "cto", "tech lead", "team lead"
    ]
    
    job_title_lower = job_title.lower()
    job_text_lower = job_text.lower()
    
    seniority_order = ["intern", "junior", "mid", "senior", "lead", "staff", "principal"]
    user_level = seniority_order.index(user_seniority) if user_seniority in seniority_order else 2
    
    is_leadership = any(s in job_title_lower for s in growth_signals)
    is_senior = "senior" in job_title_lower or "sr." in job_title_lower
    
    if is_leadership:
        score = 95
        explanation = "Leadership role - strong growth opportunity"
    elif is_senior and user_level < 3:
        score = 85
        explanation = "Senior role - promotion opportunity"
    elif is_senior and user_level >= 3:
        score = 70
        explanation = "Lateral move at senior level"
    else:
        score = 60
        explanation = "Standard role progression"
    
    return score, explanation


def _calculate_hiring_probability(
    job_text: str,
    company: str
) -> Tuple[int, str]:
    """
    Estimate probability of getting hired (0-100).
    Returns (score, explanation).
    """
    score = 50
    signals = []
    
    job_lower = job_text.lower()
    
    if "urgent" in job_lower or "immediately" in job_lower:
        score += 20
        signals.append("Urgent hiring")
    
    if "growing" in job_lower or "expanding" in job_lower:
        score += 15
        signals.append("Growing team")
    
    if "multiple openings" in job_lower or "several positions" in job_lower:
        score += 10
        signals.append("Multiple openings")
    
    if "competitive salary" in job_lower or "market rate" in job_lower:
        score += 5
        signals.append("Flexible compensation")
    
    if len(job_text) < 500:
        score -= 10
        signals.append("Minimal job details")
    
    if "5+ years" in job_lower or "7+ years" in job_lower or "10+ years" in job_lower:
        score -= 5
        signals.append("High experience requirement")
    
    score = min(100, max(20, score))
    explanation = "; ".join(signals) if signals else "Standard posting"
    
    return score, explanation


def _calculate_interest_match(
    job_text: str,
    job_title: str,
    prefs: Dict
) -> Tuple[int, str]:
    """
    Calculate interest alignment (0-100).
    Returns (score, explanation).
    """
    score = 60
    reasons = []
    
    if not prefs:
        prefs = {}
    
    if not isinstance(prefs, dict):
        prefs = {}
    
    if prefs.get("remote") and "remote" in job_text.lower():
        score += 20
        reasons.append("Remote work")
    
    if prefs.get("startup") and any(w in job_text.lower() for w in ["startup", "early stage", "seed"]):
        score += 15
        reasons.append("Startup environment")
    
    if prefs.get("enterprise") and any(w in job_text.lower() for w in ["enterprise", "fortune 500", "large scale"]):
        score += 15
        reasons.append("Enterprise environment")
    
    preferred_domains = prefs.get("domains", [])
    for domain in preferred_domains:
        if domain.lower() in job_text.lower():
            score += 10
            reasons.append(f"Domain: {domain}")
            break
    
    return min(100, max(0, score)), "; ".join(reasons) if reasons else "General match"


def calculate_opportunity_score(
    job: Dict[str, Any],
    user_profile: Dict[str, Any],
    parsed_query: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate comprehensive opportunity score for a job.
    
    Returns:
        Dict with:
        - overall_score: 0-100
        - sub_scores: {technical_fit, salary_match, career_growth, hiring_probability, interest_match}
        - matched_skills: list of skills user has
        - missing_skills: list of skills user lacks
        - skill_gaps: {skill: {time_hours, additional_jobs, salary_impact}}
        - explanations: {score_name: explanation_text}
    """
    if user_profile is None:
        user_profile = {"cv": {}, "prefs": {}}
    if parsed_query is None:
        parsed_query = {}
    
    cv = user_profile.get("cv", {}) or {}
    prefs = user_profile.get("prefs", {}) or {}
    
    user_skills = cv.get("skills", [])
    if isinstance(user_skills, str):
        user_skills = [s.strip() for s in user_skills.split(",")]
    
    user_seniority = parsed_query.get("seniority", "mid")
    
    job_title = job.get("title", "")
    job_desc = job.get("description", "")
    job_text = f"{job_title} {job_desc}"
    
    technical_score, matched_skills, missing_skills = _calculate_technical_fit(
        user_skills, job_desc, job_title
    )
    
    salary_score, salary_explanation = _calculate_salary_match(
        job.get("salary_min"),
        job.get("salary_max"),
        prefs
    )
    
    career_score, career_explanation = _calculate_career_growth(
        job_title, job_desc, user_seniority
    )
    
    hiring_score, hiring_explanation = _calculate_hiring_probability(
        job_desc, job.get("company", "")
    )
    
    interest_score, interest_explanation = _calculate_interest_match(
        job_desc, job_title, prefs
    )
    
    weights = {
        "technical_fit": 0.35,
        "salary_match": 0.20,
        "career_growth": 0.20,
        "hiring_probability": 0.10,
        "interest_match": 0.15,
    }
    
    overall = int(
        technical_score * weights["technical_fit"] +
        salary_score * weights["salary_match"] +
        career_score * weights["career_growth"] +
        hiring_score * weights["hiring_probability"] +
        interest_score * weights["interest_match"]
    )
    
    skill_gaps = {}
    for skill in missing_skills:
        skill_lower = skill.lower()
        time_hours = LEARNING_TIME_HOURS.get(skill_lower, 40)
        additional_jobs = int(time_hours / 2)
        salary_impact = int(time_hours * 5)
        
        skill_gaps[skill] = {
            "time_hours": time_hours,
            "time_display": f"{time_hours // 24} days" if time_hours >= 24 else f"{time_hours} hours",
            "additional_jobs": additional_jobs,
            "salary_impact": salary_impact,
        }
    
    return {
        "overall_score": min(100, max(0, overall)),
        "sub_scores": {
            "technical_fit": technical_score,
            "salary_match": salary_score,
            "career_growth": career_score,
            "hiring_probability": hiring_score,
            "interest_match": interest_score,
        },
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "skill_gaps": skill_gaps,
        "explanations": {
            "technical_fit": f"Matched {len(matched_skills)}/{len(matched_skills) + len(missing_skills)} required skills",
            "salary_match": salary_explanation,
            "career_growth": career_explanation,
            "hiring_probability": hiring_explanation,
            "interest_match": interest_explanation,
        },
    }


def format_opportunity_report(score_data: Dict[str, Any]) -> str:
    """Format opportunity score data into human-readable report."""
    overall = score_data["overall_score"]
    sub = score_data["sub_scores"]
    
    lines = []
    lines.append(f"**Opportunity Score: {overall}/100**")
    lines.append("")
    lines.append("**Score Breakdown:**")
    lines.append(f"- Technical Fit: {sub['technical_fit']}/100")
    lines.append(f"- Salary Match: {sub['salary_match']}/100")
    lines.append(f"- Career Growth: {sub['career_growth']}/100")
    lines.append(f"- Hiring Probability: {sub['hiring_probability']}/100")
    lines.append(f"- Interest Match: {sub['interest_match']}/100")
    
    if score_data["matched_skills"]:
        lines.append("")
        lines.append("**Your Skills That Match:**")
        for skill in score_data["matched_skills"][:5]:
            lines.append(f"+ {skill.title()}")
    
    if score_data["missing_skills"]:
        lines.append("")
        lines.append("**Skills to Learn:**")
        for skill in score_data["missing_skills"][:3]:
            gap = score_data["skill_gaps"].get(skill, {})
            time_display = gap.get("time_display", "Unknown")
            lines.append(f"- {skill.title()} ({time_display})")
    
    if score_data["missing_skills"]:
        total_hours = sum(
            score_data["skill_gaps"].get(s, {}).get("time_hours", 40)
            for s in score_data["missing_skills"]
        )
        lines.append("")
        lines.append(f"**Estimated Learning:** {total_hours} hours total")
    
    return "\n".join(lines)
