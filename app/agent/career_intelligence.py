from typing import Dict, List, Any, Optional
from agent.career_match import calculate_opportunity_score, format_opportunity_report
from agent.skill_roi import calculate_skill_roi, format_skill_roi_report
from agent.resume_simulator import simulate_resume_match, format_resume_report
from agent.career_trajectory import predict_career_trajectory, format_trajectory_report
from agent.professional_identity import extract_identity, calculate_identity_alignment


def generate_career_intelligence(
    jobs: List[Dict[str, Any]],
    user_profile: Dict[str, Any],
    parsed_query: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate comprehensive career intelligence for a set of jobs.
    
    Returns:
        Dict with:
        - current_employability: what the user can get NOW
        - opportunity_scores: list of scored jobs
        - skill_roi: ROI analysis for missing skills
        - future_trajectory: where the user is heading (separate from current)
        - summary: executive summary
    """
    cv = user_profile.get("cv", {})
    prefs = user_profile.get("prefs", {})
    identity = extract_identity(user_profile, parsed_query)
    
    scored_jobs = []
    all_missing_skills = []
    current_employability_scores = []
    
    for job in jobs:
        opportunity = calculate_opportunity_score(job, user_profile, parsed_query)
        identity_alignment = calculate_identity_alignment(identity, job)
        
        scored_job = {
            **job,
            "opportunity_score": opportunity["overall_score"],
            "sub_scores": opportunity["sub_scores"],
            "matched_skills": opportunity["matched_skills"],
            "missing_skills": opportunity["missing_skills"],
            "skill_gaps": opportunity["skill_gaps"],
            "opportunity_explanations": opportunity["explanations"],
            "identity_alignment": identity_alignment["alignment_score"],
            "identity_explanation": identity_alignment["explanation"],
        }
        scored_jobs.append(scored_job)
        all_missing_skills.extend(opportunity["missing_skills"])
        
        current_employability_scores.append(identity_alignment["alignment_score"])
    
    unique_missing = list(set(all_missing_skills))
    user_skills = cv.get("skills", [])
    if isinstance(user_skills, str):
        user_skills = [s.strip() for s in user_skills.split(",")]
    
    skill_roi = calculate_skill_roi(unique_missing, user_skills, jobs)
    
    future_trajectory = predict_career_trajectory(cv)
    
    scored_jobs.sort(key=lambda x: x["identity_alignment"], reverse=True)
    
    current_employability = _calculate_current_employability(
        identity, scored_jobs, current_employability_scores
    )
    
    summary = _generate_summary(scored_jobs, skill_roi, future_trajectory, current_employability)
    
    return {
        "current_employability": current_employability,
        "opportunity_scores": scored_jobs,
        "skill_roi": skill_roi,
        "future_trajectory": future_trajectory,
        "summary": summary,
    }


def _calculate_current_employability(
    identity: Dict[str, Any],
    scored_jobs: List[Dict],
    alignment_scores: List[int]
) -> Dict[str, Any]:
    """
    Calculate what the user can get RIGHT NOW based on their professional identity.
    This is separate from future trajectory.
    """
    headline = identity.get("headline", "Unknown")
    primary_skills = identity.get("primary_skills", [])
    
    high_alignment = sum(1 for s in alignment_scores if s >= 70)
    medium_alignment = sum(1 for s in alignment_scores if 40 <= s < 70)
    
    avg_alignment = sum(alignment_scores) / max(len(alignment_scores), 1)
    
    if avg_alignment >= 70:
        readiness = "High"
        description = f"Your profile as {headline} is well-matched to available positions."
    elif avg_alignment >= 40:
        readiness = "Medium"
        description = f"Your profile as {headline} has moderate alignment with available positions."
    else:
        readiness = "Low"
        description = f"Your profile as {headline} has limited alignment with current openings."
    
    return {
        "headline": headline,
        "readiness": readiness,
        "description": description,
        "avg_alignment": int(avg_alignment),
        "high_alignment_jobs": high_alignment,
        "medium_alignment_jobs": medium_alignment,
        "primary_skills": primary_skills,
    }


def _generate_summary(
    scored_jobs: List[Dict],
    skill_roi: List[Dict],
    future_trajectory: Dict,
    current_employability: Dict
) -> Dict[str, Any]:
    """Generate executive summary of career intelligence."""
    if not scored_jobs:
        return {
            "total_jobs": 0,
            "top_opportunities": 0,
            "avg_match": 0,
            "quick_wins": 0,
            "current_readiness": "Unknown",
            "future_path": "Unknown",
        }
    
    opp_scores = [j["identity_alignment"] for j in scored_jobs]
    avg_match = sum(opp_scores) / len(opp_scores)
    
    top_opportunities = sum(1 for s in opp_scores if s >= 60)
    
    quick_wins = sum(1 for r in skill_roi if r["roi_score"] >= 70)
    
    return {
        "total_jobs": len(scored_jobs),
        "top_opportunities": top_opportunities,
        "avg_match": int(avg_match),
        "quick_wins": quick_wins,
        "current_readiness": current_employability.get("readiness", "Unknown"),
        "current_headline": current_employability.get("headline", ""),
        "future_path": future_trajectory.get("predicted_direction", {}).get("name", "Unknown"),
        "future_confidence": future_trajectory.get("trajectory_score", 0),
    }


def format_intelligence_report(intelligence: Dict[str, Any]) -> str:
    """Format complete intelligence report into human-readable text."""
    lines = []
    
    summary = intelligence["summary"]
    
    current = intelligence.get("current_employability", {})
    lines.append("**Current Employability**")
    lines.append(f"*Identity:* {current.get('headline', 'Unknown')}")
    lines.append(f"*Readiness:* {current.get('readiness', 'Unknown')}")
    lines.append(f"*Description:* {current.get('description', '')}")
    lines.append(f"*Average Alignment:* {current.get('avg_alignment', 0)}%")
    lines.append("")
    
    lines.append("**Job Match Summary**")
    lines.append(f"- Jobs Analyzed: {summary['total_jobs']}")
    lines.append(f"- Top Opportunities: {summary['top_opportunities']} (alignment >= 60%)")
    lines.append(f"- Average Match: {summary['avg_match']}%")
    lines.append(f"- Quick Win Skills: {summary['quick_wins']}")
    lines.append("")
    
    future = intelligence.get("future_trajectory", {})
    predicted = future.get("predicted_direction")
    if predicted:
        lines.append("**Future Trajectory** (not current employability)")
        lines.append(f"- Direction: {predicted['name']}")
        lines.append(f"- Confidence: {future.get('trajectory_score', 0)}%")
        lines.append("")
    
    skill_roi = intelligence.get("skill_roi", [])
    if skill_roi:
        lines.append("**Skills to Learn ( ranked by ROI):**")
        for roi in skill_roi[:5]:
            lines.append(f"- `{roi['skill']}` ({roi['time_display']}, +${roi['salary_premium']}/mo)")
        lines.append("")
    
    opp_scores = intelligence.get("opportunity_scores", [])
    if opp_scores:
        lines.append("**Top Opportunities (by identity alignment):**")
        for job in opp_scores[:5]:
            alignment = job.get("identity_alignment", 0)
            lines.append(f"- [{alignment}%] {job['title']} @ {job.get('company', 'Unknown')}")
    
    return "\n".join(lines)
