import json
import os
import re
from openai import OpenAI
from graph.state import AgentState
from utils.normalize import word_match, find_keywords

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
    except Exception:
        pass


def _parse_query_regex(query):
    q = query.lower()

    seniority = "any"
    for level in ["senior", "junior", "intern", "lead", "staff", "principal"]:
        if level in q:
            seniority = level
            break

    work_type = ""
    if re.search(r"\bremote\b|\banywhere\b|\bworldwide\b|\bglobal\b", q):
        work_type = "remote"
    elif re.search(r"\bhybrid\b", q):
        work_type = "hybrid"
    elif re.search(r"\boffice\b|\bon-site\b|\bon site\b", q):
        work_type = "office"

    location = ""
    
    # Check for worldwide/global/anywhere patterns first
    if re.search(r"\b(worldwide|global|anywhere)\b", q):
        location = "Worldwide"
    else:
        loc_stop = r"(?:\s+(?:role|position|job|with|and|salary|posted|from|for|the|a|an|\d).*$)"
        loc_match = re.search(
            r"\bin\s+([a-z\s,]+?)" + loc_stop,
            q,
        )
        if loc_match:
            location = loc_match.group(1).strip().rstrip(",").title()
        else:
            loc_words = q.split()
            in_idx = None
            for i, w in enumerate(loc_words):
                if w == "in" and i + 1 < len(loc_words):
                    in_idx = i
                    break
            if in_idx is not None:
                after = loc_words[in_idx + 1:]
                stop_words = {"role", "position", "job", "with", "and", "salary", "posted", "from", "for", "the", "a", "an", "this", "last", "past", "today", "week", "month", "days", "day", "remote", "hybrid", "office", "worldwide", "global"}
                loc_parts = []
                for w in after:
                    w_clean = w.strip(",").strip()
                    if w_clean in stop_words or re.match(r"^\d", w_clean):
                        break
                    loc_parts.append(w_clean)
                if loc_parts:
                    location = " ".join(loc_parts).title()

    salary_min = None
    salary_max = None

    range_match = re.search(
        r"(?:min|minimum)\s*(?:salary\s*)?(?:of\s*)?(\d[\d,]*)\s.*?(?:max|maximum)\s*(?:salary\s*)?(?:of\s*)?(\d[\d,]*)",
        q
    )
    if range_match:
        salary_min = float(range_match.group(1).replace(",", ""))
        salary_max = float(range_match.group(2).replace(",", ""))
    else:
        dash_match = re.search(
            r"(\d[\d,]*)\s*[-–]\s*(\d[\d,]*)\s*(?:usd|eur|\$)",
            q
        )
        if dash_match:
            salary_min = float(dash_match.group(1).replace(",", ""))
            salary_max = float(dash_match.group(2).replace(",", ""))
        else:
            single_match = re.search(
                r"(?:salary\s*(?:of\s*)?|min(?:imum)?\s*(?:salary\s*)?(?:of\s*)?)(\d[\d,]*)\s*(?:usd|eur|\$)?",
                q
            )
            if single_match:
                val = float(single_match.group(1).replace(",", ""))
                salary_min = val
                salary_max = val
            else:
                fallback_match = re.search(
                    r"(\d[\d,]*)\s*(?:usd|eur|\$)\s*(?:per\s*month|/mo|/month)?",
                    q
                )
                if fallback_match:
                    val = float(fallback_match.group(1).replace(",", ""))
                    salary_min = val
                    salary_max = val

    posted_days = None
    if re.search(r"\btoday\b|\blast\s*24\s*h(?:ours?)?\b|\blast\s*1\s*day\b", q):
        posted_days = 1
    elif re.search(r"\bthis\s*week\b|\blast\s*7\s*days?\b|\blast\s*week\b", q):
        posted_days = 7
    elif re.search(r"\bthis\s*month\b|\blast\s*30\s*days?\b|\blast\s*month\b|\bpast\s*month\b", q):
        posted_days = 30
    else:
        m = re.search(r"\blast\s*(\d+)\s*days?\b", q)
        if m:
            posted_days = int(m.group(1))

    tech_keywords = [
        "python", "javascript", "typescript", "react", "vue", "angular",
        "node", "nodejs", "spring", "spring boot", "django", "fastapi", "flask",
        "aws", "azure", "gcp", "docker", "kubernetes", "k8s",
        "postgresql", "mysql", "mongodb", "redis",
        "machine learning", "ml", "ai", "data science", "devops", "sre",
        "golang", "rust", "ruby", "php", "swift", "kotlin",
        "terraform", "ansible", "jenkins", "ci/cd",
        "graphql", "rest", "api", "microservices",
        "java",
    ]
    found_keywords = find_keywords(q, tech_keywords)

    profession = ""
    prof_map = {
        "software engineer": ["software engineer", "software developer"],
        "java developer": ["java developer", "java engineer"],
        "data engineer": ["data engineer"],
        "data scientist": ["data scientist"],
        "frontend engineer": ["frontend engineer", "front end engineer", "frontend developer"],
        "backend engineer": ["backend engineer", "back end engineer"],
        "full stack engineer": ["full stack engineer", "fullstack engineer", "full-stack engineer"],
        "devops engineer": ["devops engineer", "devops"],
        "ml engineer": ["ml engineer", "machine learning engineer"],
        "ai engineer": ["ai engineer", "artificial intelligence engineer"],
        "mobile developer": ["mobile developer", "ios developer", "android developer"],
        "qa engineer": ["qa engineer", "quality assurance"],
        "cloud engineer": ["cloud engineer"],
        "platform engineer": ["platform engineer"],
        "site reliability engineer": ["site reliability engineer", "sre"],
    }
    for prof, triggers in prof_map.items():
        for trigger in triggers:
            if word_match(trigger, q):
                profession = prof
                break
        if profession:
            break

    if not profession:
        if word_match("developer", q):
            profession = "developer"
        elif word_match("engineer", q):
            profession = "engineer"

    if not found_keywords:
        if profession:
            found_keywords.append(profession.split()[0].lower())
        else:
            found_keywords.append("developer")

    return {
        "keywords": found_keywords if found_keywords else [],
        "seniority": seniority,
        "location": location,
        "profession": profession if profession else "Software Engineer",
        "salary_min": salary_min,
        "salary_max": salary_max,
        "work_type": work_type,
        "posted_days": posted_days,
    }


def understand_query(state: AgentState):
    query = state['query']

    if client and MODEL_ID:
        prompt = f"""
        Analyze this job search query: "{query}"

        Extract the following fields:
        - keywords: list of technical keywords/skills mentioned (e.g. ["Java", "Spring Boot"])
        - seniority: experience level ("intern", "junior", "mid", "senior", or "any")
        - location: specific location/city/country mentioned (e.g. "Tbilisi", "Georgia", "USA"). Use "Worldwide" if the query mentions worldwide/global/anywhere. Empty string if none.
        - profession: job role/type (e.g. "Software Engineer", "Data Scientist", "DevOps", "AI Engineer")
        - salary_min: minimum salary if mentioned (number, else null)
        - salary_max: maximum salary if mentioned (number, else null)
        - work_type: "remote" if remote/anywhere/worldwide/global, "hybrid" if hybrid, "office" if on-site/office, or empty string if not specified
        - posted_days: max days ago the job was posted. "today"=1, "this week"=7, "this month"=30, "last N days"=N, or null if not specified

        Return valid JSON ONLY. No other text.

        Example:
        {{
          "keywords": ["Java", "Spring Boot"],
          "seniority": "senior",
          "location": "Tbilisi",
          "profession": "Software Engineer",
          "salary_min": 4000,
          "salary_max": 5000,
          "work_type": "remote",
          "posted_days": 7
        }}
        """

        try:
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
            )
            text = response.choices[0].message.content
            if not text or not text.strip():
                print(f"[QUERY DEBUG] LLM returned empty response, using regex parser")
                parsed = _parse_query_regex(query)
                state['parsed_query'] = parsed
                return state
            text = text.strip()
            clean_json = text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_json)

            parsed.setdefault("keywords", [])
            parsed.setdefault("seniority", "any")
            parsed.setdefault("location", "")
            parsed.setdefault("profession", "")
            parsed.setdefault("salary_min", None)
            parsed.setdefault("salary_max", None)
            parsed.setdefault("work_type", "")
            parsed.setdefault("posted_days", None)

            state['parsed_query'] = parsed
            print(f"[QUERY DEBUG] LLM parsed: {parsed}")
            return state
        except Exception as e:
            print(f"[QUERY DEBUG] LLM failed ({e}), using regex parser")

    parsed = _parse_query_regex(query)
    state['parsed_query'] = parsed
    print(f"[QUERY DEBUG] Regex parsed: {parsed}")

    return state
