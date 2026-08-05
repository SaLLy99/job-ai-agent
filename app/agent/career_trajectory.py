from typing import Dict, List, Any, Optional
from agent.career_match import SKILL_CATEGORIES, _extract_skills_from_text


CAREER_PATHS = {
    "ai_infrastructure": {
        "name": "AI Infrastructure Engineer",
        "description": "Build and maintain AI/ML infrastructure, model serving, and data pipelines",
        "trajectory_skills": ["python", "kubernetes", "docker", "aws", "ml", "data engineering"],
        "growth_potential": 95,
        "salary_range": "$120k-$200k",
    },
    "backend_architect": {
        "name": "Backend Architect",
        "description": "Design scalable backend systems, microservices architecture",
        "trajectory_skills": ["java", "spring", "microservices", "distributed systems", "postgresql"],
        "growth_potential": 85,
        "salary_range": "$110k-$180k",
    },
    "platform_engineer": {
        "name": "Platform Engineer",
        "description": "Build internal developer platforms and tooling",
        "trajectory_skills": ["kubernetes", "docker", "aws", "terraform", "ci/cd"],
        "growth_potential": 88,
        "salary_range": "$115k-$190k",
    },
    "staff_engineer": {
        "name": "Staff Engineer",
        "description": "Technical leadership across multiple teams",
        "trajectory_skills": ["architecture", "mentoring", "system design", "cross-team"],
        "growth_potential": 90,
        "salary_range": "$150k-$250k",
    },
    "ai_research_engineer": {
        "name": "AI Research Engineer",
        "description": "Implement and optimize ML models, research-to-production",
        "trajectory_skills": ["python", "pytorch", "ml", "llm", "research"],
        "growth_potential": 92,
        "salary_range": "$130k-$220k",
    },
}


def predict_career_trajectory(
    user_cv: Dict[str, Any],
    recent_projects: List[str] = None,
    career_goals: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Predict user's career trajectory based on current skills and recent work.
    
    Returns:
        Dict with:
        - current_state: current skills and level
        - predicted_direction: most likely career path
        - recommended_paths: ranked list of career paths
        - skill_gaps: skills needed for each path
        - trajectory_score: confidence in prediction (0-100)
    """
    user_skills = user_cv.get("skills", [])
    if isinstance(user_skills, str):
        user_skills = [s.strip() for s in user_skills.split(",")]
    
    user_experience = user_cv.get("experience", "")
    user_projects = user_cv.get("projects", "")
    
    all_user_text = f"{user_experience} {user_projects} {' '.join(recent_projects or [])}"
    recent_skills = _extract_skills_from_text(all_user_text)
    
    skill_weights = _calculate_skill_weights(user_skills, recent_skills)
    
    path_scores = _score_career_paths(skill_weights, recent_projects or [])
    
    sorted_paths = sorted(path_scores, key=lambda x: x.get("score", 0), reverse=True)
    
    predicted_direction = sorted_paths[0] if sorted_paths else None
    
    skill_gaps = {}
    for path_id, path_data in CAREER_PATHS.items():
        path_skills = path_data["trajectory_skills"]
        missing = [s for s in path_skills if not _user_has_skill(s, user_skills, recent_skills)]
        skill_gaps[path_id] = missing
    
    trajectory_score = _calculate_trajectory_confidence(
        user_skills, recent_skills, predicted_direction
    )
    
    return {
        "current_state": {
            "skills": user_skills,
            "recent_skills": recent_skills,
            "seniority": _estimate_seniority(user_experience),
        },
        "predicted_direction": predicted_direction,
        "recommended_paths": sorted_paths[:3],
        "skill_gaps": skill_gaps,
        "trajectory_score": trajectory_score,
    }


def _calculate_skill_weights(
    user_skills: List[str],
    recent_skills: List[str]
) -> Dict[str, float]:
    """Calculate skill weights based on recency and relevance."""
    weights = {}
    
    for skill in user_skills:
        weights[skill.lower()] = 0.6
    
    for skill in recent_skills:
        skill_lower = skill.lower()
        if skill_lower in weights:
            weights[skill_lower] = min(1.0, weights[skill_lower] + 0.4)
        else:
            weights[skill_lower] = 0.8
    
    return weights


def _score_career_paths(
    skill_weights: Dict[str, float],
    recent_projects: List[str]
) -> List[Dict[str, Any]]:
    """Score each career path based on user's skills."""
    results = []
    
    for path_id, path_data in CAREER_PATHS.items():
        path_skills = path_data["trajectory_skills"]
        
        skill_score = 0
        matched_count = 0
        
        for skill in path_skills:
            weight = skill_weights.get(skill.lower(), 0)
            skill_score += weight
            if weight > 0:
                matched_count += 1
        
        if path_skills:
            skill_score = (skill_score / len(path_skills)) * 100
        else:
            skill_score = 50
        
        project_relevance = 0
        for project in recent_projects:
            project_lower = project.lower()
            for skill in path_skills:
                if skill.lower() in project_lower:
                    project_relevance += 20
        
        total_score = min(100, int(
            skill_score * 0.7 +
            min(100, project_relevance) * 0.2 +
            path_data["growth_potential"] * 0.1
        ))
        
        results.append({
            "path_id": path_id,
            "name": path_data["name"],
            "description": path_data["description"],
            "score": total_score,
            "matched_skills": matched_count,
            "total_skills": len(path_skills),
            "growth_potential": path_data["growth_potential"],
            "salary_range": path_data["salary_range"],
        })
    
    return results


def _user_has_skill(skill: str, user_skills: List[str], recent_skills: List[str]) -> bool:
    """Check if user has a skill (either in base skills or recent projects)."""
    skill_lower = skill.lower()
    
    for s in user_skills:
        if s.lower() == skill_lower:
            return True
    
    for s in recent_skills:
        if s.lower() == skill_lower:
            return True
    
    return False


def _estimate_seniority(experience: str) -> str:
    """Estimate seniority level from experience text."""
    if not experience:
        return "mid"
    
    experience_lower = experience.lower()
    
    if any(w in experience_lower for w in ["staff", "principal", "architect", "director"]):
        return "staff"
    if any(w in experience_lower for w in ["senior", "sr.", "lead"]):
        return "senior"
    if any(w in experience_lower for w in ["junior", "jr.", "entry"]):
        return "junior"
    
    import re
    years_match = re.search(r'(\d+)\+?\s*years?', experience_lower)
    if years_match:
        years = int(years_match.group(1))
        if years >= 8:
            return "staff"
        if years >= 5:
            return "senior"
        if years >= 2:
            return "mid"
        return "junior"
    
    return "mid"


def _calculate_trajectory_confidence(
    user_skills: List[str],
    recent_skills: List[str],
    predicted_direction: Optional[Dict]
) -> int:
    """Calculate confidence in trajectory prediction."""
    if not predicted_direction:
        return 30
    
    base_confidence = 50
    
    if recent_skills:
        base_confidence += 20
    
    if len(user_skills) >= 5:
        base_confidence += 10
    
    if predicted_direction["score"] >= 70:
        base_confidence += 15
    
    if predicted_direction["matched_skills"] >= 3:
        base_confidence += 10
    
    return min(100, max(20, base_confidence))


def format_trajectory_report(trajectory: Dict[str, Any]) -> str:
    """Format trajectory data into human-readable report."""
    lines = []
    
    current = trajectory["current_state"]
    lines.append(f"**Current State:** {current['seniority'].title()} level")
    lines.append(f"**Skills:** {', '.join(current['skills'][:5])}")
    lines.append("")
    
    predicted = trajectory.get("predicted_direction")
    if predicted:
        lines.append(f"**Predicted Direction:** {predicted['name']}")
        lines.append(f"**Confidence:** {trajectory['trajectory_score']}%")
        lines.append("")
    
    recommended = trajectory.get("recommended_paths", [])
    if recommended:
        lines.append("**Recommended Career Paths:**")
        for i, path in enumerate(recommended, 1):
            lines.append(f"{i}. **{path['name']}** ({path['score']}% match)")
            lines.append(f"   - {path['description']}")
            lines.append(f"   - Salary: {path['salary_range']}")
        lines.append("")
    
    gaps = trajectory.get("skill_gaps", {})
    if recommended:
        top_path = recommended[0]
        path_gaps = gaps.get(top_path["path_id"], [])
        if path_gaps:
            lines.append(f"**Skills needed for {top_path['name']}:**")
            for skill in path_gaps[:3]:
                lines.append(f"- {skill.title()}")
    
    return "\n".join(lines)
