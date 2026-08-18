from datetime import datetime, timedelta, timezone
from graph.state import AgentState
from utils.normalize import (
    experience_matches,
    salary_matches,
    location_matches as _location_matches,
    title_matches,
    word_match,
)
from agent.professional_identity import extract_identity, identity_rejects_job
import re

PROFESSION_KEYWORDS = {
    "java": ["java", "jvm", "spring", "springboot", "spring boot", "hibernate", "jpa"],
    "software_engineer": ["software engineer", "software developer", "swe", "backend engineer", "full stack engineer", "full-stack engineer"],
    "frontend": ["frontend", "front-end", "front end", "react", "vue", "angular"],
    "backend": ["backend", "back-end", "back end", "api", "server side"],
    "data": ["data engineer", "data scientist", "data analyst", "ml engineer", "machine learning"],
    "devops": ["devops", "sre", "infrastructure", "platform engineer", "cloud engineer"],
    "mobile": ["mobile", "ios", "android", "flutter", "react native"],
    "developer": ["developer", "engineer", "programmer"],
}

WORLDWIDE_SIGNALS = [
    "worldwide", "global", "anywhere", "distributed",
    "remote - worldwide", "remote (worldwide)", "remote - global",
    "any location", "no location", "location independent",
]


def _posted_within_days(job, max_days):
    if not max_days:
        return True

    posted = job.get("posted_date", "")
    if not posted:
        return True

    try:
        if isinstance(posted, str):
            posted = posted.strip()
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"):
                try:
                    dt = datetime.strptime(posted, fmt)
                    break
                except ValueError:
                    continue
            else:
                return True
        else:
            dt = posted

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=max_days)
        return dt >= cutoff
    except Exception:
        return True


GEO_RESTRICTED_REMOTE_SIGNALS = [
    "remote in ", "remote (", "remote - ",
    "remote in europe", "remote in asia", "remote in us", "remote in usa",
    "remote in uk", "remote in germany", "remote in france",
    "remote - europe", "remote - asia", "remote - us",
    "europe only", "asia only", "us only", "usa only", "uk only",
    "within timezone", "timezone overlap",
]


def _detect_job_work_type(job):
    text = f"{job.get('title', '')} {job.get('description', '')} {job.get('location', '')}".lower()

    has_office = any(w in text for w in ["on-site", "onsite", "on site", "in-office"])
    has_hybrid = "hybrid" in text
    has_remote_word = "remote" in text

    is_geo_restricted = any(signal in text for signal in GEO_RESTRICTED_REMOTE_SIGNALS)

    has_worldwide_remote = any(w in text for w in [
        "anywhere", "worldwide", "global", "distributed",
        "fully remote", "work from home", "wfh",
    ])

    # Many remote job sites don't explicitly say "remote" - if location says "Worldwide" or
    # source is a remote job board, treat as remote
    job_location = job.get("location", "").lower()
    is_worldwide_loc = any(w in job_location for w in ["worldwide", "global", "anywhere", "remote"])

    if has_hybrid:
        return "hybrid"

    if has_office and not has_remote_word:
        # "office" word in description but not explicitly remote - could be remote role
        # at a company that has offices. Be lenient.
        if is_worldwide_loc:
            return "remote"
        return "office"

    if has_worldwide_remote and not is_geo_restricted:
        return "remote"
    if has_remote_word and not is_geo_restricted and not has_office:
        return "remote"
    if has_remote_word and is_geo_restricted:
        return "remote_geo"

    # If location is worldwide/remote, assume remote even without explicit "remote" word
    if is_worldwide_loc:
        return "remote"

    return "office"


def _is_worldwide_job(job):
    job_loc = job.get("location", "").lower()
    job_text = f"{job.get('title', '')} {job.get('description', '')} {job_loc}".lower()
    return any(signal in job_text for signal in WORLDWIDE_SIGNALS)


def _job_location_matches(job, desired_location):
    job_location = job.get("location", "")
    job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    job_loc_lower = job_location.lower()

    # If user specified a location, check against it
    if desired_location:
        # Worldwide/global/anywhere queries match any job
        if desired_location.lower() in ("worldwide", "global", "anywhere"):
            return True
        
        if _location_matches(job_location, desired_location):
            return True
        # Check if job is truly worldwide
        is_worldwide = any(w in job_text for w in [
            "worldwide", "global", "anywhere", "distributed",
        ])
        if is_worldwide:
            return True
        if any(w in job_loc_lower for w in ["worldwide", "global", "anywhere"]):
            return True
        if not job_location.strip() and any(w in job_text for w in ["remote", "worldwide", "global"]):
            return True
        return False

    # No location specified (remote from anywhere) - only allow worldwide/remote jobs
    # Jobs with specific locations like "Berlin, Germany" should NOT pass
    is_worldwide_loc = any(w in job_loc_lower for w in [
        "worldwide", "global", "anywhere",
    ])
    if is_worldwide_loc:
        return True

    # "Remote" alone (no specific location) = worldwide
    if job_loc_lower in ("remote", ""):
        return True

    # Empty location + remote in text = likely worldwide
    if not job_location.strip() and any(w in job_text for w in ["remote", "worldwide", "global"]):
        return True

    # Check if job is from a remote-focused source
    source = job.get("source", "")
    remote_sources = {
        "remoteok", "weworkremotely", "wwr", "remotive",
        "workingnomads", "himalayas", "jobicy", "trulyremote",
        "nodesk", "remotehub", "remoterocketship", "remoteio",
        "levelsfyi", "levels_fyi",
    }
    if source in remote_sources:
        return True

    # Job has a specific location (e.g., "Berlin, Germany") - reject for "anywhere" query
    return False


def _stack_compatible(job, keywords, profession=""):
    if not keywords:
        return True

    title_lower = job.get("title", "").lower()
    desc_lower = job.get("description", "").lower()
    text = f"{title_lower} {desc_lower}"

    specific = [
        kw for kw in keywords
        if isinstance(kw, str) and len(kw) >= 2 and kw.lower() not in GENERIC_ROLE_WORDS
    ]

    if not specific:
        return True

    matches = sum(1 for kw in specific if word_match(kw, text))
    if matches >= 1:
        return True

    # If title is a general software/backend role, allow it through
    # even without exact keyword match - the ranker will score it lower
    general_role_keywords = [
        "backend", "back-end", "back end", "full stack", "fullstack",
        "full-stack", "software engineer", "software developer",
        "developer", "engineer", "programmer", "architect",
    ]
    if any(word_match(rk, title_lower) for rk in general_role_keywords):
        return True

    # If profession matches the title type, allow through
    if profession:
        prof_lower = profession.lower()
        prof_words = prof_lower.split()
        if any(word_match(w, title_lower) for w in prof_words if len(w) > 2):
            return True

    return False


NOISE_TOKENS = [
    "View Company Profile", "Promoted", "Boosted listing", "Boosted",
    "NewBoosted", "Featured", "Top 100", "Full-Time", "Full-Time An",
    "Full-Time", "Part-Time", "Contract", "Temporary", "Internship",
    "New", "Listing",
]

NOISE_SUFFIX_RE = re.compile(
    r'\s+(?:New|Boosted|Featured|Top\s+\d+|Full[- ]?Tim\w*|Part[- ]?Tim\w*'
    r'|Contract|Temporary|Internship|Remote|Hybrid|On[- ]?site'
    r'|\d+[dhm]\s|Posted\s+\d+).*',
    re.IGNORECASE,
)

# Pattern to remove "7d", "14d", "30d" style posted indicators
NOISE_DAYS_RE = re.compile(r'\b\d+d\b')


def _clean_title(title):
    """Strip noise prefixes and suffixes added by crawlers."""
    if not title:
        return ""
    t = title.strip()

    for token in NOISE_TOKENS:
        t = t.replace(token, "")

    t = NOISE_SUFFIX_RE.sub("", t)
    t = NOISE_DAYS_RE.sub("", t)

    t = re.sub(r'([a-z])([A-Z])', r'\1 \2', t)
    t = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', t)

    t = re.sub(r'\s{2,}', ' ', t).strip()

    return t


MISMATCHED_ROLES = {
    "product manager", "product owner", "scrum master",
    "qa engineer", "quality assurance", "tester", "test engineer",
    "account executive", "sales", "sales engineer",
    "marketing", "marketing manager", "content writer", "copywriter",
    "designer", "ui designer", "ux designer", "graphic designer",
    "project manager", "program manager",
    "hr", "human resources", "recruiter", "talent",
    "data analyst", "business analyst", "financial",
    "support engineer", "customer support", "technical support",
    "security engineer", "network engineer",
    "technical writer", "release manager",
}

GENERIC_ROLE_WORDS = {
    "developer", "engineer", "software", "programmer", "full",
    "stack", "senior", "junior", "lead", "staff", "intern",
}


def _role_compatible(job, parsed_query):
    """
    Validate that the job role matches what the user requested.
    Returns True if compatible, False if clearly mismatched.

    Strategy:
    1. If keyword in title -> PASS
    2. If title is clearly a different role (PM, QA, Sales...) -> FAIL
    3. Otherwise -> PASS (generic titles like "Software Engineer" are OK)
    """
    if not parsed_query:
        return True

    keywords = parsed_query.get("keywords", [])
    profession = parsed_query.get("profession", "")

    if not keywords and not profession:
        return True

    raw_title = (job.get("title") or "")
    job_title = _clean_title(raw_title).lower()
    original_lower = raw_title.lower()

    if title_matches(raw_title, parsed_query):
        return True

    if keywords:
        specific_keywords = [
            kw for kw in keywords
            if isinstance(kw, str) and len(kw) >= 2 and kw.lower() not in GENERIC_ROLE_WORDS
        ]
        for kw in specific_keywords:
            if word_match(kw, job_title):
                return True

    if profession:
        prof_lower = profession.lower()
        if word_match(prof_lower, job_title):
            return True

    # Check for clearly mismatched roles - but only if they are the PRIMARY role
    # e.g., "QA Engineer" should be rejected for a Java Developer search,
    # but "Backend Developer PHP" should NOT be rejected
    primary_role_words = job_title.split()
    for mismatch in MISMATCHED_ROLES:
        mismatch_words = mismatch.split()
        # Only reject if the mismatched role is the primary focus of the title
        if len(mismatch_words) <= 1:
            # Single word mismatches (like "sales", "designer", "hr")
            if word_match(mismatch, job_title):
                return False
        else:
            # Multi-word mismatches - check if all words appear near each other
            if all(word_match(w, job_title) for w in mismatch_words):
                return False

    return True


def filter_jobs(state: AgentState):
    jobs = state.get('validated_jobs', state.get('scraped_jobs', []))
    parsed = state.get('parsed_query', {})

    print(f"[FILTER DEBUG] Input jobs: {len(jobs)}, parsed_query: {parsed}")

    if not jobs:
        state['filtered_jobs'] = []
        return state

    if not parsed:
        state['filtered_jobs'] = jobs
        return state

    user_profile = state.get('user_profile', {})
    identity = extract_identity(user_profile, parsed)
    has_identity = bool(identity.get("primary_skills") or identity.get("headline"))

    desired_location = parsed.get("location", "")
    keywords = parsed.get("keywords", [])
    seniority = parsed.get("seniority", "any")
    profession = parsed.get("profession", "")
    salary_min = parsed.get("salary_min")
    salary_max = parsed.get("salary_max")
    desired_work_type = parsed.get("work_type", "")
    posted_days = parsed.get("posted_days")

    is_worldwide_query = desired_location.lower() in ("worldwide", "global", "anywhere")

    print(f"[FILTER DEBUG] location={desired_location}, keywords={keywords}, seniority={seniority}, profession={profession}, work_type={desired_work_type}, posted_days={posted_days}, worldwide={is_worldwide_query}")
    print(f"[FILTER DEBUG] Identity: headline={identity.get('headline','')}, primary={identity.get('primary_skills',[])}, reject_if={identity.get('reject_if',{})}")

    filtered = []
    work_type_dropped = 0
    location_dropped = 0
    title_dropped = 0
    seniority_dropped = 0
    date_dropped = 0
    role_dropped = 0
    identity_dropped = 0

    for idx, job in enumerate(jobs):
        job_title = job.get("title", "")
        job_desc = job.get("description", "")
        job_company = job.get("company", "")
        job_text = f"{job_title} {job_desc} {job_company}".lower()

        job_work_type = _detect_job_work_type(job)
        drop_reason = None

        reject_reason = identity_rejects_job(identity, job) if has_identity else None
        if reject_reason:
            drop_reason = f"identity({reject_reason})"
            identity_dropped += 1

        if not drop_reason and not _role_compatible(job, parsed):
            drop_reason = "role_mismatch"
            role_dropped += 1

        if not drop_reason and desired_work_type:
            if is_worldwide_query:
                pass
            elif desired_work_type == "remote":
                if job_work_type == "office":
                    # Double-check: if the job is from a remote-focused site or
                    # has worldwide location, allow it through even if detected as office
                    job_loc = job.get("location", "").lower()
                    is_worldwide_loc = any(w in job_loc for w in [
                        "worldwide", "global", "anywhere", "remote",
                    ])
                    source = job.get("source", "")
                    remote_sources = {
                        "remoteok", "weworkremotely", "wwr", "remotive",
                        "workingnomads", "himalayas", "jobicy", "trulyremote",
                        "nodesk", "remotehub", "remoterocketship", "remoteio",
                        "levelsfyi", "levels_fyi",
                    }
                    # Allow jobs from remote sources even if detected as office
                    if is_worldwide_loc or source in remote_sources:
                        pass  # Allow through
                    else:
                        drop_reason = f"work_type(office!=remote)"
                        work_type_dropped += 1
                elif job_work_type == "remote_geo":
                    # Allow geo-restricted remote for worldwide queries
                    if is_worldwide_query:
                        pass
                    else:
                        drop_reason = f"work_type(geo_restricted_remote)"
                        work_type_dropped += 1
            elif desired_work_type == "hybrid":
                if job_work_type not in ("hybrid", "remote"):
                    drop_reason = f"work_type({job_work_type}!={desired_work_type})"
                    work_type_dropped += 1
            elif desired_work_type == "office":
                pass

        if not drop_reason:
            loc_lower = desired_location.lower() if desired_location else ""
            is_remote_loc = loc_lower in ("remote", "anywhere")

            if not is_worldwide_query and desired_location and not is_remote_loc:
                # User specified a location (e.g., "Tbilisi") — check match
                if not _job_location_matches(job, desired_location):
                    drop_reason = f"location({job.get('location','')})"
                    location_dropped += 1
            elif not desired_location or is_remote_loc:
                # User said "anywhere" or no location — only allow worldwide/remote jobs
                if not _job_location_matches(job, ""):
                    drop_reason = f"location({job.get('location','')})"
                    location_dropped += 1

        if not drop_reason and keywords:
            if not _stack_compatible(job, keywords, profession):
                drop_reason = f"stack(no keyword match)"
                title_dropped += 1

        if not drop_reason and seniority and seniority != "any":
            if not experience_matches(job_text, seniority):
                drop_reason = f"seniority({seniority})"
                seniority_dropped += 1

        if not drop_reason and (salary_min or salary_max):
            if not salary_matches(job_text, salary_min, salary_max):
                drop_reason = "salary"

        if not drop_reason and posted_days:
            if not _posted_within_days(job, posted_days):
                drop_reason = f"date({posted_days}d)"
                date_dropped += 1

        if idx < 5:
            status = "KEPT" if not drop_reason else f"DROPPED({drop_reason})"
            print(f"  [{idx}] {job_title!r} | work={job_work_type} | loc={job.get('location','')} | {status}")

        if not drop_reason:
            filtered.append(job)

    print(f"[FILTER DEBUG] Output: {len(filtered)} jobs. Dropped: identity={identity_dropped}, work_type={work_type_dropped}, location={location_dropped}, title={title_dropped}, seniority={seniority_dropped}, date={date_dropped}, role={role_dropped}")

    state['filtered_jobs'] = filtered
    return state
