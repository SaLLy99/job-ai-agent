from graph.state import AgentState
from utils.normalize import location_matches, title_matches, experience_matches, word_match
from graph.nodes.filter_jobs import _detect_job_work_type


def _verify_job(job, parsed_query):
    """
    Check if a ranked job actually matches the user's request.
    Returns (passes, match_breakdown).
    """
    breakdown = {}
    job_location = job.get("location", "")

    keywords = parsed_query.get("keywords", [])
    if keywords:
        job_text = f"{job.get('title', '')} {job.get('description', '')}"
        role_ok = False
        for kw in keywords:
            if isinstance(kw, str) and len(kw) > 2:
                if word_match(kw, job_text):
                    role_ok = True
                    break
        if not role_ok:
            role_ok = title_matches(job.get("title", ""), parsed_query)
        # If the job is a general software/backend role, allow it through
        # even without exact keyword match
        if not role_ok:
            title_lower = job.get("title", "").lower()
            general_roles = [
                "software engineer", "software developer", "backend",
                "back-end", "full stack", "fullstack", "developer",
                "engineer", "architect",
            ]
            if any(word_match(r, title_lower) for r in general_roles):
                role_ok = True
        # If no description available, be lenient on role check
        if not role_ok and not job.get("description"):
            role_ok = True
        breakdown["role"] = "pass" if role_ok else "fail"
    else:
        breakdown["role"] = "pass"

    desired_location = parsed_query.get("location", "")
    if desired_location:
        work_type = parsed_query.get("work_type", "")
        if work_type == "remote":
            job_text = f"{job.get('title', '')} {job.get('description', '')} {job_location}".lower()
            is_remote = any(w in job_text for w in ["remote", "worldwide", "global", "anywhere", "distributed"])
            loc_ok = is_remote or location_matches(job_location, desired_location)
        else:
            loc_ok = location_matches(job_location, desired_location)
        breakdown["location"] = "pass" if loc_ok else "fail"
    else:
        breakdown["location"] = "pass"

    desired_work_type = parsed_query.get("work_type", "")
    if desired_work_type:
        job_wt = _detect_job_work_type(job)
        if desired_work_type == "remote":
            wt_ok = job_wt in ("remote", "remote_geo")
            # If detected as office but has no location info, be lenient
            if not wt_ok and job_wt == "office":
                job_loc = job.get("location", "").lower()
                if not job_loc or job_loc in ("", "worldwide", "global", "anywhere"):
                    wt_ok = True
        elif desired_work_type == "hybrid":
            wt_ok = job_wt in ("hybrid", "remote")
        elif desired_work_type == "office":
            wt_ok = job_wt == "office"
        else:
            wt_ok = True
        breakdown["work_type"] = "pass" if wt_ok else "fail"
    else:
        breakdown["work_type"] = "pass"

    desired_seniority = parsed_query.get("seniority", "any")
    if desired_seniority and desired_seniority != "any":
        job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        sen_ok = experience_matches(job_text, desired_seniority)
        breakdown["seniority"] = "pass" if sen_ok else "fail"
    else:
        breakdown["seniority"] = "pass"

    passes = all(v == "pass" for v in breakdown.values())
    return passes, breakdown


def verify_results(state: AgentState):
    """
    Post-rank verification.
    Removes jobs that don't actually match the user's request.
    """
    ranked_jobs = state.get("ranked_jobs", [])
    parsed_query = state.get("parsed_query", {})

    if not ranked_jobs:
        state["verified_jobs"] = []
        return state

    MIN_SCORE = 1
    verified = []
    removed = []

    for job in ranked_jobs:
        job_score = job.get("score", 0)
        if job_score < MIN_SCORE:
            removed.append({
                "title": job.get("title", "?"),
                "company": job.get("company", "?"),
                "reason": f"Score too low ({job_score}/{MIN_SCORE})",
            })
            print(
                f"[VERIFY] Removed: {job.get('title', '?')} ({job.get('company', '?')}) "
                f"- score {job_score} below minimum {MIN_SCORE}"
            )
            continue

        passes, breakdown = _verify_job(job, parsed_query)

        if passes:
            job["match_breakdown"] = breakdown
            verified.append(job)
        else:
            failed = [k for k, v in breakdown.items() if v == "fail"]
            removed.append({
                "title": job.get("title", "?"),
                "company": job.get("company", "?"),
                "reason": f"Failed: {', '.join(failed)}",
            })
            print(
                f"[VERIFY] Removed: {job.get('title', '?')} ({job.get('company', '?')}) "
                f"- {', '.join(failed)} mismatch"
            )

    state["verified_jobs"] = verified

    if removed:
        state["rejection_log"] = state.get("rejection_log", []) + removed

    print(f"[VERIFY] {len(verified)} passed, {len(removed)} removed from {len(ranked_jobs)} ranked")

    return state
