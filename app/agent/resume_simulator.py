import re
from typing import Dict, List, Any, Tuple
from agent.career_match import _extract_skills_from_text, SKILL_CATEGORIES


def simulate_resume_match(
    user_cv: Dict[str, Any],
    job: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Simulate how well a resume matches a job posting.
    
    Returns:
        Dict with:
        - current_match: 0-100 percentage
        - suggested_improvements: list of {skill, impact} items
        - new_match: 0-100 after improvements
        - detailed_breakdown: dict of matching areas
    """
    user_skills = user_cv.get("skills", [])
    if isinstance(user_skills, str):
        user_skills = [s.strip() for s in user_skills.split(",")]
    
    user_experience = user_cv.get("experience", "")
    user_education = user_cv.get("education", "")
    user_projects = user_cv.get("projects", "")
    
    job_title = job.get("title", "")
    job_desc = job.get("description", "")
    job_text = f"{job_title} {job_desc}"
    
    job_skills = _extract_skills_from_text(job_text)
    
    matched_skills = []
    missing_skills = []
    
    for skill in job_skills:
        skill_lower = skill.lower()
        user_has = any(s.lower() == skill_lower for s in user_skills)
        
        if user_has:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)
    
    skill_match_ratio = len(matched_skills) / len(job_skills) if job_skills else 0.5
    
    experience_keywords = _extract_experience_keywords(job_text)
    user_exp_text = f"{user_experience} {user_projects}".lower()
    matched_experience = [kw for kw in experience_keywords if kw in user_exp_text]
    
    experience_match_ratio = len(matched_experience) / len(experience_keywords) if experience_keywords else 0.5
    
    current_match = int(
        (skill_match_ratio * 60) +
        (experience_match_ratio * 40)
    )
    
    improvements = _calculate_improvements(
        missing_skills, job_skills, job_text, user_skills
    )
    
    potential_additional = sum(imp["impact"] for imp in improvements[:3])
    new_match = min(100, current_match + potential_additional)
    
    return {
        "current_match": min(100, max(0, current_match)),
        "suggested_improvements": improvements,
        "new_match": min(100, max(0, new_match)),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "detailed_breakdown": {
            "skills": {
                "matched": len(matched_skills),
                "total": len(job_skills),
                "percentage": int(skill_match_ratio * 100),
            },
            "experience": {
                "matched": len(matched_experience),
                "total": len(experience_keywords),
                "percentage": int(experience_match_ratio * 100),
            },
        },
    }


def _extract_experience_keywords(text: str) -> List[str]:
    """Extract experience-related keywords from job text."""
    patterns = [
        r'\b\d+\+?\s*years?\b',
        r'\b(?:senior|lead|principal|architect)\b',
        r'\b(?:microservices?|distributed systems?|cloud)\b',
        r'\b(?:agile|scrum|kanban)\b',
        r'\b(?:ci/cd|devops|automation)\b',
        r'\b(?:team lead|tech lead|mentoring)\b',
    ]
    
    keywords = []
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        keywords.extend(matches)
    
    return list(set(keywords))


def _calculate_improvements(
    missing_skills: List[str],
    job_skills: List[str],
    job_text: str,
    user_skills: List[str]
) -> List[Dict[str, Any]]:
    """Calculate suggested improvements and their impact."""
    improvements = []
    
    skill_importance = _calculate_skill_importance(missing_skills, job_text)
    
    for skill in missing_skills:
        importance = skill_importance.get(skill, 50)
        
        impact = int(importance * 0.4)
        
        is_core = skill.lower() in job_text.lower().split()[:100]
        if is_core:
            impact = min(30, impact + 10)
        
        improvements.append({
            "skill": skill.title(),
            "impact": min(30, max(5, impact)),
            "importance": importance,
            "reason": _get_improvement_reason(skill, job_text),
        })
    
    improvements.sort(key=lambda x: x["impact"], reverse=True)
    
    return improvements


def _calculate_skill_importance(skills: List[str], job_text: str) -> Dict[str, int]:
    """Calculate importance of each skill based on job text."""
    importance = {}
    
    lines = job_text.lower().split('\n')
    
    for skill in skills:
        skill_lower = skill.lower()
        score = 50
        
        title_match = skill_lower in job_text[:200].lower()
        if title_match:
            score += 30
        
        requirement_section = False
        for line in lines:
            if any(w in line for w in ["requirement", "qualif", "must have", "required"]):
                requirement_section = True
            
            if requirement_section and skill_lower in line:
                score += 20
                break
        
        importance[skill] = min(100, score)
    
    return importance


def _get_improvement_reason(skill: str, job_text: str) -> str:
    """Generate reason for why this skill matters."""
    skill_lower = skill.lower()
    
    if skill_lower in job_text[:500].lower():
        return f"Mentioned early in job description"
    
    if any(w in skill_lower for w in ["kafka", "redis", "microservices"]):
        return "Key infrastructure skill"
    
    if any(w in skill_lower for w in ["spring", "react", "django"]):
        return "Core framework requirement"
    
    if any(w in skill_lower for w in ["aws", "gcp", "azure"]):
        return "Cloud platform skill"
    
    return "Listed in requirements"


def format_resume_report(resume_data: Dict[str, Any]) -> str:
    """Format resume simulation data into human-readable report."""
    current = resume_data["current_match"]
    new_match = resume_data["new_match"]
    improvements = resume_data["suggested_improvements"]
    
    lines = []
    lines.append(f"**Resume Match: {current}%**")
    lines.append("")
    
    if improvements:
        lines.append("**Quick wins to improve your match:**")
        for imp in improvements[:3]:
            lines.append(f"+ Mention `{imp['skill']}` (+{imp['impact']}%)")
        
        lines.append("")
        lines.append(f"**After improvements: {new_match}%**")
    
    breakdown = resume_data.get("detailed_breakdown", {})
    if breakdown:
        skills = breakdown.get("skills", {})
        exp = breakdown.get("experience", {})
        lines.append("")
        lines.append(f"**Skills match:** {skills.get('matched', 0)}/{skills.get('total', 0)} ({skills.get('percentage', 0)}%)")
        lines.append(f"**Experience match:** {exp.get('matched', 0)}/{exp.get('total', 0)} ({exp.get('percentage', 0)}%)")
    
    return "\n".join(lines)
