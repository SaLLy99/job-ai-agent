import os
import json
import re
from openai import OpenAI
from graph.nodes.filter_jobs import (
    _detect_job_work_type,
    _is_worldwide_job,
    _posted_within_days,
)
from utils.normalize import clean_salary, normalize_currency, salary_matches, word_match
from agent.career_match import calculate_opportunity_score
from agent.professional_identity import extract_identity, calculate_identity_alignment


GROQ_KEY = os.getenv("JOB_PLATFORM_API_KEY")

client = None
MODEL_ID = None

if GROQ_KEY:
    try:
        client = OpenAI(
            api_key=GROQ_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        MODEL_ID = "llama-3.3-70b-versatile"
        print("[LLM DEBUG] Groq initialized")
    except Exception as e:
        print(f"[LLM DEBUG] Groq init failed: {e}")


class Ranker:

    def _heuristic_rank(self, profile, jobs, query, parsed_query=None):
        if parsed_query is None:
            parsed_query = {}
        if not profile:
            profile = {"cv": {}, "prefs": {}}
        if not isinstance(profile, dict):
            profile = {"cv": {}, "prefs": {}}
        if "cv" not in profile:
            profile["cv"] = {}
        if "prefs" not in profile:
            profile["prefs"] = {}

        identity = extract_identity(profile, parsed_query)
        has_identity = bool(identity.get("primary_skills") or identity.get("headline"))

        query_keywords = parsed_query.get("keywords", [])
        seniority = parsed_query.get("seniority", "any")
        location = parsed_query.get("location", "")
        desired_work_type = parsed_query.get("work_type", "")
        salary_min = parsed_query.get("salary_min")
        salary_max = parsed_query.get("salary_max")
        posted_days = parsed_query.get("posted_days")
        is_worldwide = location.lower() in ("worldwide", "global", "anywhere")

        specific_keywords = [kw.lower() for kw in query_keywords if isinstance(kw, str) and len(kw) > 2]

        scored = []
        skipped_low_alignment = 0
        skipped_low_score = 0

        for job in jobs:
            title = str(job.get("title", "")).lower()
            description = str(job.get("description", "")).lower()
            company = str(job.get("company", "")).lower()
            job_location = str(job.get("location", "")).lower()

            identity_alignment = calculate_identity_alignment(identity, job)
            alignment_score = identity_alignment["alignment_score"]

            # 60% similarity threshold - skip jobs below this
            if has_identity and alignment_score < 20:
                skipped_low_alignment += 1
                continue

            score = 0

            if has_identity:
                score += alignment_score * 0.3

            title_kw_hits = 0
            desc_kw_hits = 0
            for kw in specific_keywords:
                if word_match(kw, title):
                    score += 3
                    title_kw_hits += 1
                elif word_match(kw, description):
                    score += 1
                    desc_kw_hits += 1

            if title_kw_hits >= 2:
                score += 2

            if seniority and seniority != "any":
                sen_pattern = re.compile(r'\b' + re.escape(seniority) + r'\b')
                if sen_pattern.search(title):
                    score += 3
                elif sen_pattern.search(description):
                    score += 1

            if not is_worldwide and location:
                loc_lower = location.lower()
                loc_pattern = re.compile(r'\b' + re.escape(loc_lower) + r'\b')
                if loc_pattern.search(job_location):
                    score += 4
                elif _is_worldwide_job(job):
                    score += 2

            if desired_work_type:
                job_wt = _detect_job_work_type(job)
                if desired_work_type == "remote" and job_wt == "remote":
                    score += 3
                elif desired_work_type == "remote" and job_wt == "remote_geo":
                    pass
                elif desired_work_type == "hybrid" and job_wt in ("hybrid", "remote"):
                    score += 1
                elif desired_work_type == "office" and job_wt == "office":
                    score += 1

            if salary_min or salary_max:
                job_text = f"{title} {description} {company}"
                job_salary = clean_salary(job_text)
                job_min_usd = normalize_currency(job_salary["salary_min"], job_salary["currency"])
                job_max_usd = normalize_currency(job_salary["salary_max"], job_salary["currency"])

                if job_min_usd is not None and job_max_usd is not None:
                    if salary_min and job_max_usd < salary_min:
                        score -= 3
                    elif salary_max and job_min_usd > salary_max:
                        score -= 3
                    else:
                        score += 2

            if posted_days:
                if _posted_within_days(job, posted_days):
                    score += 1

            if score > 0:
                score_clamped = min(100, max(1, int(score)))
                
                # 60% similarity threshold - convert to percentage
                similarity_pct = min(100, max(0, int(score * 2)))  # Scale score to percentage

                opportunity = calculate_opportunity_score(job, profile, parsed_query)

                scored.append({
                    "title": job.get("title", "Untitled Role"),
                    "company": job.get("company", "Unknown"),
                    "url": job.get("url", ""),
                    "description": job.get("description", ""),
                    "source": job.get("source", "Web"),
                    "location": job.get("location", ""),
                    "salary_min": job.get("salary_min"),
                    "salary_max": job.get("salary_max"),
                    "currency": job.get("currency"),
                    "score": score_clamped,
                    "similarity_pct": similarity_pct,
                    "identity_alignment": alignment_score,
                    "identity_explanation": identity_alignment["explanation"],
                    "matched_primary_skills": identity_alignment["matched_primary"],
                    "matched_secondary_skills": identity_alignment["matched_secondary"],
                    "opportunity_score": opportunity["overall_score"],
                    "sub_scores": opportunity["sub_scores"],
                    "matched_skills": opportunity["matched_skills"],
                    "missing_skills": opportunity["missing_skills"],
                    "skill_gaps": opportunity["skill_gaps"],
                    "opportunity_explanations": opportunity["explanations"],
                    "why": self._build_reason(
                        job,
                        query,
                        profile,
                        parsed_query,
                        identity,
                        identity_alignment
                    ),
                })
            else:
                skipped_low_score += 1
                if skipped_low_score <= 5:
                    kw_hit = any(word_match(kw, title) for kw in specific_keywords)
                    print(f"  [RANK] SKIP score={score:.1f} kw_hit={kw_hit} title={job.get('title','')[:80]}")

        print(f"[RANK DEBUG] Heuristic: {len(scored)} scored, {skipped_low_alignment} skipped (low alignment), {skipped_low_score} skipped (low score)")

        print(f"[RANK DEBUG] Heuristic: {len(scored)} scored, {skipped_low_alignment} skipped (low alignment), {skipped_low_score} skipped (low score)")

        scored.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return {
            "results": scored[:10]
        }


    def _build_reason(self, job, query, profile, parsed_query=None, identity=None, identity_alignment=None):
        if parsed_query is None:
            parsed_query = {}

        title = str(job.get("title", "")).strip()
        description = str(job.get("description", "")).lower()

        keywords = parsed_query.get("keywords", [])
        location = parsed_query.get("location", "")

        reasons = []

        if identity_alignment:
            matched_primary = identity_alignment.get("matched_primary", [])
            matched_secondary = identity_alignment.get("matched_secondary", [])
            if matched_primary:
                reasons.append(f"primary skills match: {', '.join(matched_primary[:3])}")
            if matched_secondary:
                reasons.append(f"secondary skills: {', '.join(matched_secondary[:2])}")
            if identity_alignment.get("primary_match"):
                headline = identity.get("headline", "") if identity else ""
                if headline:
                    reasons.append(f"aligns with: {headline}")

        if keywords:
            title_matched = []
            desc_matched = []
            for kw in keywords:
                if isinstance(kw, str) and len(kw) > 2:
                    if word_match(kw, title.lower()):
                        title_matched.append(kw)
                    elif word_match(kw, description):
                        desc_matched.append(kw)

            if title_matched:
                reasons.append(f"query keywords in title: {', '.join(title_matched[:3])}")
            if desc_matched:
                reasons.append(f"query keywords in description: {', '.join(desc_matched[:3])}")

        if location and location.lower() in str(
            job.get("location", "")
        ).lower():
            reasons.append(
                f"located in {location}"
            )

        if reasons:
            return (
                f"Strong match - {'; '.join(reasons)}."
            )

        return (
            f"Matches your search for '{query}'."
        )


    def rank(self, profile, jobs, query, parsed_query=None):

        if not jobs:
            return {
                "results": []
            }

        if not profile:
            profile = {"cv": {}, "prefs": {}}
        if not isinstance(profile, dict):
            profile = {"cv": {}, "prefs": {}}
        if "cv" not in profile:
            profile["cv"] = {}
        if "prefs" not in profile:
            profile["prefs"] = {}

        print(
            f"[RANK DEBUG] Input jobs: {len(jobs)}, query: {query}"
        )


        if client and MODEL_ID:

            heuristic_candidates = self._heuristic_rank(
                profile,
                jobs,
                query,
                parsed_query
            )

            jobs_for_llm = heuristic_candidates["results"][:20]
            print(f"[RANK DEBUG] Heuristic produced {len(jobs_for_llm)} candidates for LLM")

            if not jobs_for_llm:
                print(f"[RANK DEBUG] No heuristic candidates, skipping LLM")
                return heuristic_candidates


            prompt = f"""
You are a job ranking engine.

PROFESSIONAL IDENTITY:
{json.dumps(extract_identity(profile, parsed_query))}

USER PROFILE:
{json.dumps(profile)}

SEARCH QUERY:
{query}

EXTRACTED CRITERIA:
{json.dumps(parsed_query or {})}

JOBS TO RANK:
{json.dumps(jobs_for_llm)}

TASK:
Rank jobs from best to worst match for THIS professional identity.

SCORING RULES:
- Primary signal: Does the job match the professional headline and primary skills?
- A job requiring PHP/Ruby/SharePoint when the user is a Java Backend Engineer = REJECT (score 0)
- A job matching primary skills (Java, Spring Boot, Microservices) = HIGH score
- A job matching secondary skills (AWS, Kubernetes, AI) = MEDIUM score
- Location, salary, seniority are secondary signals

NEVER rank a job highly just because it mentions ANY of the user's skills.
The job must align with the professional identity as a whole.

RULES:
- Never infer missing information.
- If a field is unknown (salary, location), keep it as null.
- Do not guess salary from seniority, company, or market averages.
- Do not guess location from company HQ or timezone.
- If salary info is missing, leave salary_min/salary_max as null.

Return ONLY valid JSON.

FORMAT:

{{
  "results": [
    {{
      "title": "",
      "company": "",
      "url": "",
      "description": "",
      "source": "",
      "location": "",
      "salary_min": null,
      "salary_max": null,
      "currency": null,
      "score": 0,
      "why": ""
    }}
  ]
}}
"""


            try:

                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0
                )


                text = (
                    response
                    .choices[0]
                    .message
                    .content
                )

                if not text or not text.strip():
                    print(
                        f"[RANK DEBUG] LLM returned empty response, using heuristic"
                    )
                    return self._heuristic_rank(
                        profile,
                        jobs,
                        query,
                        parsed_query
                    )

                text = text.strip()


                text = (
                    text
                    .replace("```json", "")
                    .replace("```", "")
                    .strip()
                )


                parsed = json.loads(text)


                if (
                    isinstance(parsed, dict)
                    and parsed.get("results")
                ):

                    results = []
                    seen = set()


                    for r in parsed["results"]:

                        key = (
                            r.get("title", "").lower()
                            +
                            r.get("company", "").lower()
                        )

                        job_score = r.get("score", 0)
                        if not isinstance(job_score, (int, float)):
                            job_score = 0

                        if key not in seen and job_score >= 0:
                            seen.add(key)
                            if r.get("salary_min") is None:
                                r["salary_min"] = None
                            if r.get("salary_max") is None:
                                r["salary_max"] = None
                            if r.get("currency") is None:
                                r["currency"] = None
                            results.append(r)


                    print(
                        f"[RANK DEBUG] LLM ranked {len(results)} jobs"
                    )

                    # If LLM returned all zero scores, fall back to heuristic
                    if results and all(r.get("score", 0) == 0 for r in results):
                        print(f"[RANK DEBUG] LLM returned all zero scores, using heuristic")
                        return self._heuristic_rank(
                            profile,
                            jobs,
                            query,
                            parsed_query
                        )

                    return {
                        "results": results[:10]
                    }


            except Exception as e:

                print(
                    f"[RANK DEBUG] LLM failed ({e}), using heuristic"
                )


        return self._heuristic_rank(
            profile,
            jobs,
            query,
            parsed_query
        )
