from typing import Dict, List, Any, Optional
from agent.career_match import SKILL_CATEGORIES, LEARNING_TIME_HOURS, _extract_skills_from_text


SKILL_MARKET_DATA = {
    "java": {"demand_score": 85, "avg_salary_premium": 500},
    "python": {"demand_score": 95, "avg_salary_premium": 600},
    "javascript": {"demand_score": 90, "avg_salary_premium": 450},
    "typescript": {"demand_score": 88, "avg_salary_premium": 500},
    "go": {"demand_score": 82, "avg_salary_premium": 700},
    "rust": {"demand_score": 78, "avg_salary_premium": 800},
    "react": {"demand_score": 92, "avg_salary_premium": 500},
    "vue": {"demand_score": 75, "avg_salary_premium": 400},
    "angular": {"demand_score": 70, "avg_salary_premium": 350},
    "spring": {"demand_score": 80, "avg_salary_premium": 450},
    "spring boot": {"demand_score": 85, "avg_salary_premium": 500},
    "nodejs": {"demand_score": 88, "avg_salary_premium": 450},
    "django": {"demand_score": 72, "avg_salary_premium": 400},
    "fastapi": {"demand_score": 78, "avg_salary_premium": 450},
    "aws": {"demand_score": 90, "avg_salary_premium": 600},
    "gcp": {"demand_score": 82, "avg_salary_premium": 550},
    "azure": {"demand_score": 85, "avg_salary_premium": 550},
    "docker": {"demand_score": 88, "avg_salary_premium": 400},
    "kubernetes": {"demand_score": 85, "avg_salary_premium": 550},
    "kafka": {"demand_score": 78, "avg_salary_premium": 600},
    "redis": {"demand_score": 80, "avg_salary_premium": 350},
    "postgresql": {"demand_score": 82, "avg_salary_premium": 400},
    "mysql": {"demand_score": 75, "avg_salary_premium": 300},
    "mongodb": {"demand_score": 70, "avg_salary_premium": 350},
    "microservices": {"demand_score": 85, "avg_salary_premium": 550},
    "ai": {"demand_score": 95, "avg_salary_premium": 800},
    "machine learning": {"demand_score": 92, "avg_salary_premium": 750},
    "llm": {"demand_score": 98, "avg_salary_premium": 900},
    "devops": {"demand_score": 88, "avg_salary_premium": 600},
    "data engineering": {"demand_score": 85, "avg_salary_premium": 650},
}


def calculate_skill_roi(
    missing_skills: List[str],
    user_skills: List[str],
    all_jobs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Calculate ROI for learning each missing skill.
    
    Returns list of skill ROI items sorted by ROI score.
    """
    if not missing_skills or not all_jobs:
        return []
    
    skill_rois = []
    
    for skill in missing_skills:
        skill_lower = skill.lower()
        
        time_hours = LEARNING_TIME_HOURS.get(skill_lower, 40)
        market_data = SKILL_MARKET_DATA.get(skill_lower, {"demand_score": 50, "avg_salary_premium": 300})
        
        jobs_requiring = 0
        jobs_that_become_eligible = 0
        
        for job in all_jobs:
            job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
            has_skill = skill_lower in job_text
            
            if has_skill:
                jobs_requiring += 1
                
                user_has_required = False
                for user_skill in user_skills:
                    if user_skill.lower() in job_text:
                        user_has_required = True
                        break
                
                if not user_has_required:
                    jobs_that_become_eligible += 1
        
        demand_score = market_data["demand_score"]
        salary_premium = market_data["avg_salary_premium"]
        
        if time_hours > 0:
            roi_score = int(
                (demand_score * 0.4) +
                (min(100, jobs_requiring * 2) * 0.3) +
                (min(100, salary_premium / 10) * 0.3)
            )
        else:
            roi_score = 50
        
        skill_rois.append({
            "skill": skill.title(),
            "time_hours": time_hours,
            "time_display": _format_time(time_hours),
            "demand_score": demand_score,
            "jobs_requiring": jobs_requiring,
            "jobs_that_become_eligible": jobs_that_become_eligible,
            "salary_premium": salary_premium,
            "roi_score": min(100, max(0, roi_score)),
        })
    
    skill_rois.sort(key=lambda x: x["roi_score"], reverse=True)
    
    return skill_rois


def _format_time(hours: int) -> str:
    """Format hours into human-readable string."""
    if hours < 24:
        return f"{hours} hours"
    days = hours // 24
    remaining = hours % 24
    if remaining > 0:
        return f"{days} days {remaining}h"
    return f"{days} days"


def format_skill_roi_report(skill_rois: List[Dict[str, Any]]) -> str:
    """Format skill ROI data into human-readable report."""
    if not skill_rois:
        return "No skill gaps identified."
    
    lines = []
    lines.append("**Learning ROI Analysis:**")
    lines.append("")
    
    for i, roi in enumerate(skill_rois[:5], 1):
        lines.append(f"**{i}. {roi['skill']}**")
        lines.append(f"   - Time: {roi['time_display']}")
        lines.append(f"   - Market demand: {roi['demand_score']}/100")
        lines.append(f"   - Jobs requiring: {roi['jobs_requiring']}")
        lines.append(f"   - Salary premium: +${roi['salary_premium']}/month")
        lines.append(f"   - ROI Score: {roi['roi_score']}/100")
        lines.append("")
    
    total_hours = sum(r["time_hours"] for r in skill_rois)
    total_premium = sum(r["salary_premium"] for r in skill_rois)
    lines.append(f"**Total Learning:** {_format_time(total_hours)}")
    lines.append(f"**Potential Salary Increase:** +${total_premium}/month")
    
    return "\n".join(lines)
