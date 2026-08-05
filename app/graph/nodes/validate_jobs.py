from graph.state import AgentState
from utils.normalize import clean_salary


def _validate_job(job):
    """Validate a single job. Returns (is_valid, reason)."""
    title = (job.get("title") or "").strip()
    if len(title) < 5:
        return False, "title_too_short"

    if not job.get("source"):
        return False, "missing_source"

    if not job.get("url"):
        return False, "missing_url"

    return True, None


def validate_jobs(state: AgentState):
    """
    Pre-rank validation gate.
    Validates job data quality and cleans salary fields.
    Rejects jobs with missing required fields.
    Tracks per-crawler stats.
    """
    raw_jobs = state.get("scraped_jobs", [])
    crawler_stats = {}

    validated = []
    rejected = []

    for job in raw_jobs:
        source = job.get("source", "unknown")

        if source not in crawler_stats:
            crawler_stats[source] = {"total": 0, "validated": 0, "rejected": 0}
        crawler_stats[source]["total"] += 1

        is_valid, reason = _validate_job(job)

        if not is_valid:
            crawler_stats[source]["rejected"] += 1
            rejected.append({
                "title": job.get("title", "?"),
                "company": job.get("company", "?"),
                "source": source,
                "reason": reason,
            })
            continue

        salary_data = clean_salary(
            f"{job.get('title', '')} {job.get('description', '')} {job.get('location', '')}"
        )
        job["salary_min"] = salary_data["salary_min"]
        job["salary_max"] = salary_data["salary_max"]
        job["currency"] = salary_data["currency"]

        crawler_stats[source]["validated"] += 1
        validated.append(job)

    state["validated_jobs"] = validated

    for r in rejected:
        print(f"[VALIDATE] Rejected: {r['title']!r} ({r['source']}) - {r['reason']}")

    for source, stats in crawler_stats.items():
        print(
            f"[VALIDATE] {source}: {stats['total']} total, "
            f"{stats['validated']} valid, {stats['rejected']} rejected"
        )

    state["crawler_stats"] = crawler_stats
    state["rejection_log"] = rejected

    return state
