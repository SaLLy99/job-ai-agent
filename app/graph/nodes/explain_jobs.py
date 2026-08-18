from graph.state import AgentState
from db.repository import Repository
from collections import Counter


def explain_jobs(state: AgentState):
    """
    Format final response with match breakdown per job.
    Persists crawler stats to DB.
    """
    verified_jobs = state.get('verified_jobs', [])
    ranked_jobs = state.get('ranked_jobs', [])
    parsed_query = state.get('parsed_query', {})

    jobs_to_show = verified_jobs if verified_jobs else ranked_jobs

    count = len(jobs_to_show)

    if count == 0:
        state['final_response'] = "I couldn't find any jobs matching your criteria. Try adjusting your search."
    elif count == 1:
        state['final_response'] = f"I found 1 job that matches your request."
    else:
        state['final_response'] = f"I found {count} jobs that match your request."

    # Add source breakdown
    source_counts = Counter(job.get("source", "Unknown") for job in jobs_to_show)
    if source_counts:
        source_breakdown = ", ".join(f"{src}: {cnt}" for src, cnt in source_counts.most_common())
        state['final_response'] += f"\n\nSources: {source_breakdown}"

    for job in jobs_to_show:
        breakdown = job.get("match_breakdown", {})

        role_status = "Exact match" if breakdown.get("role") == "pass" else "Partial match"
        location_status = "Confirmed" if breakdown.get("location") == "pass" else "Unknown"
        work_type_status = "Confirmed" if breakdown.get("work_type") == "pass" else "Unknown"
        seniority_status = "Match" if breakdown.get("seniority") == "pass" else "Unknown"

        salary_min = job.get("salary_min")
        salary_max = job.get("salary_max")
        currency = job.get("currency")
        if salary_min is not None or salary_max is not None:
            salary_status = f"{currency or ''} {salary_min or '?'}-{salary_max or '?'}"
        else:
            salary_status = "Unknown"

        score = job.get("score", 0)
        confidence = min(95, max(20, score * 10))

        job["formatted_breakdown"] = (
            f"Role: {role_status}\n"
            f"Location: {location_status}\n"
            f"Salary: {salary_status}\n"
            f"Remote: {work_type_status}\n"
            f"Source: {job.get('source', 'Unknown')}\n"
            f"Confidence: {confidence}%"
        )

    crawler_stats = state.get("crawler_stats", {})
    if crawler_stats:
        try:
            repo = Repository()
            repo.save_batch_crawler_stats(crawler_stats)
        except Exception as e:
            print(f"[EXPLAIN] Failed to save crawler stats: {e}")

    rejection_log = state.get("rejection_log", [])
    if rejection_log:
        print(f"[EXPLAIN] {len(rejection_log)} jobs rejected during pipeline")

    return state
