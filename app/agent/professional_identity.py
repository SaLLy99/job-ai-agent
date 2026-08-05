"""
Professional Identity module.

Captures who the user IS as a professional, not just what skills they have.
This drives the entire matching algorithm.
"""

import re
from typing import Dict, List, Any, Optional

# Default professional identity structure
DEFAULT_IDENTITY = {
    "headline": "",
    "primary_skills": [],
    "secondary_skills": [],
    "reject_if": {
        "languages": [],
        "frameworks": [],
        "roles": [],
        "keywords": [],
    },
    "target_roles": [],
    "experience_years": None,
    "min_salary": None,
    "preferred_work_type": "",
    "preferred_locations": [],
    "timezone_overlap": "",
}


def extract_identity(profile: Dict[str, Any], parsed_query: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Extract professional identity from user profile.
    Falls back to defaults if identity is missing.
    Uses parsed_query as last resort for skills inference.
    """
    if not profile:
        profile = {}

    cv = profile.get("cv", {}) or {}
    prefs = profile.get("prefs", {}) or {}
    identity = profile.get("identity", {}) or {}

    headline = identity.get("headline", "")
    if not headline:
        headline = _infer_headline(cv, parsed_query)

    primary_skills = identity.get("primary_skills", [])
    if not primary_skills:
        primary_skills = cv.get("skills", [])[:5] if cv.get("skills") else []
    if not primary_skills and parsed_query:
        primary_skills = _infer_skills_from_query(parsed_query)

    secondary_skills = identity.get("secondary_skills", [])

    reject_if = identity.get("reject_if", {})
    if not reject_if or not any(reject_if.values()):
        reject_if = _infer_reject_rules(cv, primary_skills)

    target_roles = identity.get("target_roles", [])
    experience_years = identity.get("experience_years") or _infer_experience_years(cv)
    min_salary = identity.get("min_salary") or prefs.get("salary_min")
    preferred_work_type = identity.get("preferred_work_type") or prefs.get("work_type", "")
    preferred_locations = identity.get("preferred_locations", [])
    timezone_overlap = identity.get("timezone_overlap", "")

    return {
        "headline": headline,
        "primary_skills": [s.lower() for s in primary_skills],
        "secondary_skills": [s.lower() for s in secondary_skills],
        "reject_if": {
            "languages": [s.lower() for s in reject_if.get("languages", [])],
            "frameworks": [s.lower() for s in reject_if.get("frameworks", [])],
            "roles": [s.lower() for s in reject_if.get("roles", [])],
            "keywords": [s.lower() for s in reject_if.get("keywords", [])],
        },
        "target_roles": [s.lower() for s in target_roles],
        "experience_years": experience_years,
        "min_salary": min_salary,
        "preferred_work_type": preferred_work_type,
        "preferred_locations": [s.lower() for s in preferred_locations],
        "timezone_overlap": timezone_overlap,
    }


def _infer_skills_from_query(parsed_query: Dict[str, Any]) -> list:
    """Infer primary skills from the search query keywords."""
    keywords = parsed_query.get("keywords", [])
    profession = parsed_query.get("profession", "")

    skill_map = {
        "java": ["java", "spring boot", "spring", "microservices"],
        "python": ["python", "django", "fastapi"],
        "javascript": ["javascript", "node.js", "react"],
        "typescript": ["typescript", "react", "node.js"],
        "react": ["react", "javascript", "typescript"],
        "angular": ["angular", "typescript"],
        "vue": ["vue", "javascript"],
        "go": ["go", "golang"],
        "rust": ["rust"],
        "ruby": ["ruby", "rails"],
        "php": ["php", "laravel"],
        "kotlin": ["kotlin", "java"],
        "swift": ["swift"],
        "devops": ["devops", "aws", "docker", "kubernetes"],
        "data": ["python", "sql", "spark"],
        "ai": ["python", "machine learning", "ai"],
        "ml": ["python", "machine learning", "ai"],
    }

    inferred = []
    for kw in keywords:
        kw_lower = kw.lower() if isinstance(kw, str) else ""
        if kw_lower in skill_map:
            inferred.extend(skill_map[kw_lower])
        elif len(kw_lower) > 2:
            inferred.append(kw_lower)

    if not inferred and profession:
        prof_lower = profession.lower()
        for key in skill_map:
            if key in prof_lower:
                inferred.extend(skill_map[key])
                break

    seen = set()
    result = []
    for s in inferred:
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result[:5]


def _infer_headline(cv: Dict[str, Any], parsed_query: Dict[str, Any] = None) -> str:
    """Infer a professional headline from CV data and query."""
    skills = cv.get("skills", [])
    experience = cv.get("experience", "")
    profession = ""
    seniority = ""
    if parsed_query:
        profession = parsed_query.get("profession", "")
        seniority = parsed_query.get("seniority", "")

    all_skills = [s.lower() for s in skills]
    if not all_skills and parsed_query:
        all_skills = _infer_skills_from_query(parsed_query)

    if not all_skills and not profession:
        return ""

    skill_set = set(all_skills)

    backend_signals = {"java", "spring", "spring boot", "python", "go", "rust", "kotlin", "microservices", "distributed systems"}
    frontend_signals = {"react", "vue", "angular", "javascript", "typescript", "next.js"}
    ai_signals = {"ai", "machine learning", "ml", "llm", "deep learning", "nlp"}
    devops_signals = {"aws", "kubernetes", "docker", "terraform", "ci/cd", "devops"}

    has_backend = bool(backend_signals & skill_set)
    has_frontend = bool(frontend_signals & skill_set)
    has_ai = bool(ai_signals & skill_set)
    has_devops = bool(devops_signals & skill_set)

    parts = []
    if seniority and seniority != "any":
        parts.append(seniority.title())

    if has_backend:
        parts.append("Backend Engineer")
    elif has_frontend:
        parts.append("Fullstack Engineer")
    elif has_ai:
        parts.append("AI Engineer")
    elif has_devops:
        parts.append("Platform Engineer")
    elif profession:
        parts.append(profession)
    else:
        parts.append("Software Engineer")

    return " ".join(parts) if parts else "Software Engineer"


REJECTED_COMPANIES = {"toptal", "proxify"}


def _infer_reject_rules(cv: Dict[str, Any], primary_skills: List[str]) -> Dict[str, List[str]]:
    """Infer rejection rules from CV and primary skills."""
    skills_lower = [s.lower() for s in cv.get("skills", [])]

    reject_languages = []
    reject_frameworks = []
    reject_keywords = []

    known_backend_languages = {"java", "python", "go", "rust", "kotlin", "c#", "scala"}
    known_frontend_languages = {"javascript", "typescript"}
    known_other_languages = {"php", "ruby", "swift", "objective-c"}

    user_backend = known_backend_languages & set(skills_lower)
    user_frontend = known_frontend_languages & set(skills_lower)

    if user_backend and not user_frontend:
        if "php" not in skills_lower:
            reject_languages.extend(["php"])
        if "ruby" not in skills_lower:
            reject_languages.extend(["ruby"])

    if "laravel" not in skills_lower and "php" not in skills_lower:
        reject_frameworks.append("laravel")
    if "rails" not in skills_lower and "ruby" not in skills_lower:
        reject_frameworks.append("rails")
    if "sharepoint" not in skills_lower:
        reject_frameworks.append("sharepoint")

    reject_keywords.extend(["toptal", "proxify"])

    return {
        "languages": reject_languages,
        "frameworks": reject_frameworks,
        "roles": [],
        "keywords": reject_keywords,
    }


def _infer_experience_years(cv: Dict[str, Any]) -> Optional[int]:
    """Try to infer years of experience from CV text."""
    experience = cv.get("experience", "")
    if not experience:
        return None

    import re
    match = re.search(r'(\d+)\+?\s*years?', str(experience).lower())
    if match:
        return int(match.group(1))
    return None


def identity_rejects_job(identity: Dict[str, Any], job: Dict[str, Any]) -> Optional[str]:
    """
    Check if professional identity explicitly rejects this job.
    Returns rejection reason string, or None if not rejected.
    """
    reject_if = identity.get("reject_if", {})
    job_title = (job.get("title", "") or "").lower()
    job_desc = (job.get("description", "") or "").lower()
    job_text = f"{job_title} {job_desc}"

    for lang in reject_if.get("languages", []):
        if lang and _requires_language(lang, job_text):
            return f"Requires {lang.title()} (not in your stack)"

    for framework in reject_if.get("frameworks", []):
        if framework and _requires_framework(framework, job_text):
            return f"Requires {framework.title()} (not in your stack)"

    for role in reject_if.get("roles", []):
        if role and role in job_title:
            return f"Role mismatch: {role}"

    for keyword in reject_if.get("keywords", []):
        if keyword and keyword in job_text:
            return f"Contains excluded keyword: {keyword}"

    return None


def _requires_language(lang: str, job_text: str) -> bool:
    """Check if a job REQUIRES a specific language (not just mentions it)."""
    from utils.normalize import word_match

    require_patterns = [
        rf"required.*\b{re.escape(lang)}\b",
        rf"\b{re.escape(lang)}\b.*required",
        rf"must.*\b{re.escape(lang)}\b",
        rf"\b{re.escape(lang)}\b.*must have",
        rf"primary.*\b{re.escape(lang)}\b",
        rf"main.*\b{re.escape(lang)}\b",
        rf"\b{re.escape(lang)}\b.*backend",
    ]

    for pattern in require_patterns:
        if re.search(pattern, job_text):
            return True

    title_lower = job_text.split("\n")[0] if "\n" in job_text else job_text[:100]
    if word_match(lang, title_lower):
        return True

    return False


def _requires_framework(framework: str, job_text: str) -> bool:
    """Check if a job REQUIRES a specific framework."""
    from utils.normalize import word_match

    require_patterns = [
        rf"required.*\b{re.escape(framework)}\b",
        rf"\b{re.escape(framework)}\b.*required",
        rf"must.*\b{re.escape(framework)}\b",
        rf"primary.*\b{re.escape(framework)}\b",
    ]

    for pattern in require_patterns:
        if re.search(pattern, job_text):
            return True

    title_lower = job_text.split("\n")[0] if "\n" in job_text else job_text[:100]
    if word_match(framework, title_lower):
        return True

    return False


def calculate_identity_alignment(
    identity: Dict[str, Any],
    job: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate how well a job aligns with professional identity.

    Returns:
        {
            "alignment_score": 0-100,
            "primary_match": bool,
            "secondary_match": bool,
            "matched_primary": [...],
            "matched_secondary": [...],
            "explanation": str,
        }
    """
    job_title = (job.get("title", "") or "").lower()
    job_desc = (job.get("description", "") or "").lower()
    job_text = f"{job_title} {job_desc}"

    primary_skills = identity.get("primary_skills", [])
    secondary_skills = identity.get("secondary_skills", [])
    target_roles = identity.get("target_roles", [])

    # Skill matching with aliases
    SKILL_ALIASES = {
        "java": ["java", "jvm", "spring", "springboot", "spring boot", "hibernate", "jpa", "kotlin"],
        "spring boot": ["spring boot", "springboot", "spring"],
        "spring": ["spring", "spring boot", "springboot", "spring framework"],
        "microservices": ["microservices", "microservice", "distributed systems", "api"],
        "python": ["python", "django", "fastapi", "flask"],
        "javascript": ["javascript", "js", "node", "nodejs", "node.js", "typescript", "react", "vue", "angular"],
        "react": ["react", "reactjs", "react.js", "nextjs", "next.js"],
        "aws": ["aws", "amazon web services", "ec2", "s3", "lambda"],
        "docker": ["docker", "container", "containers"],
        "kubernetes": ["kubernetes", "k8s"],
    }

    def _skill_matches(skill, text):
        """Check if skill matches text via exact or alias."""
        skill_lower = skill.lower()
        if skill_lower in text:
            return True
        for alias in SKILL_ALIASES.get(skill_lower, []):
            if alias in text:
                return True
        return False

    matched_primary = [s for s in primary_skills if _skill_matches(s, job_text)]
    matched_secondary = [s for s in secondary_skills if _skill_matches(s, job_text)]

    primary_ratio = len(matched_primary) / max(len(primary_skills), 1)
    secondary_ratio = len(matched_secondary) / max(len(secondary_skills), 1)

    # Role matching
    role_match = False
    GENERAL_ROLE_KEYWORDS = [
        "software engineer", "software developer", "backend", "back-end",
        "full stack", "fullstack", "developer", "engineer", "architect",
        "senior", "lead", "staff",
    ]
    for role in target_roles:
        if role.lower() in job_title:
            role_match = True
            break

    # Check if job is a general software/backend role (even without exact skill match)
    is_general_role = any(kw in job_title for kw in GENERAL_ROLE_KEYWORDS)

    if role_match:
        alignment = 60 + (primary_ratio * 30) + (secondary_ratio * 10)
    elif primary_ratio >= 0.5:
        alignment = 40 + (primary_ratio * 40) + (secondary_ratio * 10)
    elif primary_ratio >= 0.25:
        alignment = 20 + (primary_ratio * 30) + (secondary_ratio * 10)
    elif is_general_role:
        # General software/backend role - give base alignment even without skill match
        alignment = 15 + (primary_ratio * 15) + (secondary_ratio * 5)
    else:
        alignment = primary_ratio * 10 + secondary_ratio * 3

    primary_match = primary_ratio >= 0.25
    secondary_match = secondary_ratio > 0

    explanation_parts = []
    if role_match:
        explanation_parts.append(f"Target role match")
    if matched_primary:
        explanation_parts.append(f"Primary skills: {', '.join(matched_primary[:3])}")
    if matched_secondary:
        explanation_parts.append(f"Secondary: {', '.join(matched_secondary[:2])}")
    if is_general_role and not matched_primary:
        explanation_parts.append(f"General software/backend role")
    if not explanation_parts:
        explanation_parts.append("Low identity alignment")

    return {
        "alignment_score": min(100, max(0, int(alignment))),
        "primary_match": primary_match,
        "secondary_match": secondary_match,
        "matched_primary": matched_primary,
        "matched_secondary": matched_secondary,
        "explanation": "; ".join(explanation_parts),
    }
