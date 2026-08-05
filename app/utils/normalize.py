import re


def word_match(keyword, text):
    """Check if keyword appears as a whole word in text (not as substring of another word)."""
    if not keyword or not text:
        return False
    pattern = re.compile(r'\b' + re.escape(keyword.lower()) + r'\b')
    return pattern.search(text.lower()) is not None


def find_keywords(text, keywords):
    """Find all keywords that appear as whole words in text."""
    if not text or not keywords:
        return []
    return [kw for kw in keywords if word_match(kw, text)]


TITLE_KEYWORDS = {
    "java": ["java", "jvm", "spring", "springboot", "spring boot", "hibernate", "jpa"],
    "software_engineer": ["software engineer", "software developer", "swe", "backend engineer", "full stack engineer", "full-stack engineer"],
    "frontend": ["frontend", "front-end", "front end", "react", "vue", "angular"],
    "backend": ["backend", "back-end", "back end", "api", "server side"],
    "ai": ["ai", "artificial intelligence", "machine learning", "ml engineer", "deep learning", "nlp", "llm", "generative ai", "gen ai"],
    "data": ["data engineer", "data scientist", "data analyst"],
    "devops": ["devops", "sre", "infrastructure", "platform engineer", "cloud engineer"],
    "mobile": ["mobile", "ios", "android", "flutter", "react native"],
}

EXPERIENCE_LEVELS = {
    "intern": ["intern", "internship", "trainee"],
    "junior": ["junior", "jr", "entry level", "entry-level", "graduate"],
    "mid": ["mid level", "mid-level", "mid", "intermediate"],
    "senior": ["senior", "sr", "lead", "staff", "principal"],
}

SALARY_PATTERNS = [
    r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*k\s*[-–]\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*k",
    r"\$\s*(\d{1,3}(?:,\d{3})*)\s*[-–]\s*\$\s*(\d{1,3}(?:,\d{3})*)",
    r"(\d{1,3}(?:,\d{3})*)\s*[-–]\s*(\d{1,3}(?:,\d{3})*)\s*(?:usd|eur|gbp)",
    r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*k",
    r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:per year|/year|/yr|annual|annually)",
    r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:per month|/month|/mo)",
    r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:usd|eur|gbp)\s*(?:per year|/year|/yr|annual|annually)?",
]


def normalize_location(text):
    if not text:
        return ""
    return text.lower().strip()


def normalize_title(title):
    if not title:
        return ""
    title = title.lower().strip()
    categories = []
    for category, keywords in TITLE_KEYWORDS.items():
        for kw in keywords:
            if word_match(kw, title):
                categories.append(category)
                break
    return categories


def extract_salary(text):
    if not text:
        return None
    for pattern in SALARY_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            matched_text = text[match.start():match.end() + 10].lower()
            has_k = "k" in matched_text
            try:
                if len(groups) == 2 and groups[1]:
                    low = float(groups[0].replace(",", ""))
                    high = float(groups[1].replace(",", ""))
                    if has_k:
                        low *= 1000
                        high *= 1000
                    return (low, high)
                else:
                    val = float(groups[0].replace(",", ""))
                    if has_k:
                        val *= 1000
                    return (val, val)
            except (ValueError, IndexError):
                continue
    return None


def parse_experience_level(text):
    if not text:
        return "any"
    text = text.lower().strip()

    for level in ["senior", "junior", "intern", "mid"]:
        for kw in EXPERIENCE_LEVELS[level]:
            if word_match(kw, text):
                return level
    return "any"


def location_matches(job_location, desired_location):
    if not desired_location or desired_location == "any":
        return True
    if not job_location:
        return True

    job_loc = normalize_location(job_location)
    desired = normalize_location(desired_location)

    if desired in job_loc or job_loc in desired:
        return True

    return False


def title_matches(job_title, parsed_query):
    if not parsed_query:
        return True

    keywords = parsed_query.get("keywords", [])
    if not keywords:
        return True

    job_title_lower = job_title.lower() if job_title else ""
    job_categories = normalize_title(job_title)

    for keyword in keywords:
        kw_lower = keyword.lower()
        if word_match(kw_lower, job_title_lower):
            return True
        for cat, cat_keywords in TITLE_KEYWORDS.items():
            if kw_lower in cat_keywords or kw_lower == cat:
                if cat in job_categories:
                    return True

    return False


def experience_matches(job_text, desired_level):
    if not desired_level or desired_level == "any":
        return True
    if not job_text:
        return True

    job_level = parse_experience_level(job_text)
    if job_level == "any":
        return True

    level_order = ["intern", "junior", "mid", "senior", "staff", "principal"]
    try:
        desired_idx = level_order.index(desired_level)
        job_idx = level_order.index(job_level)
        return abs(desired_idx - job_idx) <= 1
    except ValueError:
        return True


def salary_matches(job_text, desired_min, desired_max):
    if not desired_min and not desired_max:
        return True
    if not job_text:
        return True

    job_salary = extract_salary(job_text)
    if not job_salary:
        return True

    job_min, job_max = job_salary
    if desired_min and job_max < desired_min:
        return False
    if desired_max and job_min > desired_max:
        return False
    return True


# ============================================================
# NEW: Zero-guessing salary extraction
# ============================================================

VAGUE_SALARY_TERMS = [
    "competitive", "market rate", "market-rate", "good salary",
    "great salary", "attractive", "negotiable", "depending on experience",
    "doe", "commensurate", "benefits package", "equity",
]

CURRENCY_SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "₾": "GEL",
}

CURRENCY_KEYWORDS = {
    "usd": "USD", "dollar": "USD", "dollars": "USD",
    "eur": "EUR", "euro": "EUR", "euros": "EUR",
    "gbp": "GBP", "pound": "GBP", "pounds": "GBP", "sterling": "GBP",
    "gel": "GEL", "lari": "GEL",
}

CURRENCY_TO_USD = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
    "GEL": 0.37,
}


def clean_salary(text):
    """
    Extract salary from text with zero guessing.
    Returns {salary_min, salary_max, currency} or all None if unknown.
    Never infers salary from context.
    """
    if not text:
        return {"salary_min": None, "salary_max": None, "currency": None}

    text_lower = text.lower().strip()

    for term in VAGUE_SALARY_TERMS:
        if term in text_lower:
            return {"salary_min": None, "salary_max": None, "currency": None}

    detected_currency = None
    for symbol, curr in CURRENCY_SYMBOLS.items():
        if symbol in text:
            detected_currency = curr
            break
    if not detected_currency:
        for keyword, curr in CURRENCY_KEYWORDS.items():
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                detected_currency = curr
                break

    clean_text = text
    for sym in CURRENCY_SYMBOLS:
        clean_text = clean_text.replace(sym, '')

    range_match = re.search(
        r'(\d[\d,]*k?)\s*[-–—to]+\s*(\d[\d,]*k?)',
        clean_text
    )
    if range_match:
        try:
            low_str = range_match.group(1).replace(",", "").replace("k", "").replace("K", "")
            high_str = range_match.group(2).replace(",", "").replace("k", "").replace("K", "")
            low = float(low_str)
            high = float(high_str)
            if "k" in range_match.group(1).lower():
                low *= 1000
            if "k" in range_match.group(2).lower():
                high *= 1000
            if low > 0 and high > 0:
                return {"salary_min": low, "salary_max": high, "currency": detected_currency}
        except (ValueError, IndexError):
            pass

    single_match = re.search(
        r'(\d[\d,]*k?)',
        clean_text
    )
    if single_match:
        try:
            raw = single_match.group(1).replace(",", "")
            has_k_in_match = "k" in raw.lower()
            val_str = raw.replace("k", "").replace("K", "")
            val = float(val_str)
            if has_k_in_match:
                val *= 1000
            if val > 0:
                return {"salary_min": val, "salary_max": val, "currency": detected_currency}
        except (ValueError, IndexError):
            pass

    return {"salary_min": None, "salary_max": None, "currency": None}


def normalize_currency(amount, currency):
    """Convert a salary amount to USD. Returns None if currency unknown."""
    if amount is None or currency is None:
        return None
    rate = CURRENCY_TO_USD.get(currency.upper())
    if rate is None:
        return None
    return amount * rate


# ============================================================
# IMPROVED: Location matching with country mappings
# ============================================================

COUNTRY_TO_CITIES = {
    "georgia": ["tbilisi", "batumi", "kutaisi", "rustavi", "gori", "poti", "zugdidi"],
    "germany": ["berlin", "munich", "hamburg", "frankfurt", "cologne", "dusseldorf", "stuttgart", "leipzig", "dresden", "bonn"],
    "usa": ["new york", "san francisco", "los angeles", "chicago", "seattle", "austin", "boston", "denver", "miami", "atlanta", "dallas", "houston", "portland", "phoenix", "detroit", "minneapolis", "san diego", "nashville", "raleigh", "charlotte"],
    "united states": ["new york", "san francisco", "los angeles", "chicago", "seattle", "austin", "boston", "denver", "miami", "atlanta", "dallas", "houston", "portland", "phoenix"],
    "uk": ["london", "manchester", "birmingham", "edinburgh", "glasgow", "bristol", "leeds", "liverpool", "cambridge", "oxford"],
    "united kingdom": ["london", "manchester", "birmingham", "edinburgh", "glasgow", "bristol", "leeds", "liverpool"],
    "canada": ["toronto", "vancouver", "montreal", "calgary", "ottawa", "edmonton", "waterloo", "quebec"],
    "france": ["paris", "lyon", "marseille", "toulouse", "nice", "bordeaux", "nantes", "strasbourg"],
    "netherlands": ["amsterdam", "rotterdam", "the hague", "utrecht", "eindhoven", "groningen"],
    "spain": ["madrid", "barcelona", "valencia", "seville", "bilbao", "malaga"],
    "italy": ["rome", "milan", "turin", "naples", "florence", "bologna"],
    "portugal": ["lisbon", "porto", "braga", "coimbra"],
    "ireland": ["dublin", "cork", "galway", "limerick"],
    "poland": ["warsaw", "krakow", "wroclaw", "gdansk", "poznan", "katowice"],
    "czech republic": ["prague", "brno", "ostrava"],
    "czechia": ["prague", "brno", "ostrava"],
    "switzerland": ["zurich", "geneva", "basel", "bern", "lausanne"],
    "austria": ["vienna", "graz", "linz", "salzburg"],
    "sweden": ["stockholm", "gothenburg", "malmo", "uppsala"],
    "norway": ["oslo", "bergen", "trondheim", "stavanger"],
    "denmark": ["copenhagen", "aarhus", "odense"],
    "finland": ["helsinki", "espoo", "tampere", "turku"],
    "israel": ["tel aviv", "jerusalem", "haifa", "petah tikva"],
    "india": ["bangalore", "mumbai", "delhi", "hyderabad", "pune", "chennai", "kolkata", "ahmedabad"],
    "japan": ["tokyo", "osaka", "kyoto", "yokohama"],
    "australia": ["sydney", "melbourne", "brisbane", "perth", "adelaide", "canberra"],
    "brazil": ["sao paulo", "rio de janeiro", "belo horizonte", "curitiba", "brasilia"],
    "argentina": ["buenos aires", "cordoba", "rosario"],
    "mexico": ["mexico city", "guadalajara", "monterrey"],
    "singapore": ["singapore"],
    "south korea": ["seoul", "busan", "incheon"],
    "remote": ["remote", "worldwide", "global", "anywhere"],
}

CITY_TO_COUNTRY = {}
for country, cities in COUNTRY_TO_CITIES.items():
    for city in cities:
        CITY_TO_COUNTRY[city.strip().lower()] = country

# Country aliases for flexible matching
COUNTRY_ALIASES = {
    "usa": "united states",
    "us": "united states",
    "u.s.": "united states",
    "u.s.a.": "united states",
    "uk": "united kingdom",
    "u.k.": "united kingdom",
    "uae": "united arab emirates",
    "dubai": "united arab emirates",
    "nl": "netherlands",
    "de": "germany",
    "fr": "france",
    "es": "spain",
    "it": "italy",
    "pt": "portugal",
    "ie": "ireland",
    "pl": "poland",
    "cz": "czech republic",
    "ch": "switzerland",
    "at": "austria",
    "se": "sweden",
    "no": "norway",
    "dk": "denmark",
    "fi": "finland",
    "in": "india",
    "jp": "japan",
    "au": "australia",
    "br": "brazil",
    "ar": "argentina",
    "mx": "mexico",
    "sg": "singapore",
    "kr": "south korea",
    "ca": "canada",
}


def _normalize_country(name):
    """Normalize country name to canonical form."""
    name = name.lower().strip()
    return COUNTRY_ALIASES.get(name, name)

REMOTE_SIGNALS = {"remote", "worldwide", "global", "anywhere", "distributed", "work from home", "wfh"}

# Patterns like "Remote in Europe", "Remote in Germany", "Remote - Berlin"
REMOTE_IN_PATTERN = re.compile(r"remote\s+(?:in|[-–—])\s+(.+)", re.IGNORECASE)


def _extract_remote_in_location(job_location):
    """Extract location from 'Remote in Berlin' or 'Remote - Germany' patterns."""
    match = REMOTE_IN_PATTERN.search(job_location)
    if match:
        return match.group(1).strip().lower()
    return None


def location_matches(job_location, desired_location):
    """
    Deterministic location matching. No LLM involved.
    Returns True if job location satisfies desired location.
    """
    if not desired_location or desired_location.strip().lower() in ("any", ""):
        return True
    if not job_location:
        return True

    job_loc = normalize_location(job_location)
    desired = normalize_location(desired_location)

    # Direct substring match
    if desired in job_loc or job_loc in desired:
        return True

    # Remote in location patterns (e.g., "Remote in Europe" matches "Europe")
    remote_in_loc = _extract_remote_in_location(job_loc)
    if remote_in_loc:
        if desired in remote_in_loc or remote_in_loc in desired:
            return True
        desired_country = _normalize_country(CITY_TO_COUNTRY.get(desired, desired))
        remote_in_country = _normalize_country(CITY_TO_COUNTRY.get(remote_in_loc, remote_in_loc))
        if desired_country == remote_in_country:
            return True

    # Check city -> country mapping
    desired_country = _normalize_country(CITY_TO_COUNTRY.get(desired, desired))
    job_country = _normalize_country(CITY_TO_COUNTRY.get(job_loc, job_loc))

    if desired_country == job_country and desired_country != desired:
        return True

    # Check job location parts - split by comma first (handles "San Francisco, CA")
    job_parts = [p.strip() for p in job_loc.split(",")]
    for part in job_parts:
        part_country = _normalize_country(CITY_TO_COUNTRY.get(part, ""))
        if part_country and part_country == desired_country:
            return True
        # Also check sub-parts (e.g., "San Francisco" from "San Francisco, CA")
        sub_parts = part.split()
        for sub in sub_parts:
            sub_country = _normalize_country(CITY_TO_COUNTRY.get(sub, ""))
            if sub_country and sub_country == desired_country:
                return True

    # Check desired location parts
    desired_parts = [p.strip() for p in desired.split(",")]
    for part in desired_parts:
        part_country = _normalize_country(CITY_TO_COUNTRY.get(part, ""))
        if part_country:
            for jp in job_parts:
                jp_country = _normalize_country(CITY_TO_COUNTRY.get(jp, ""))
                if jp_country and jp_country == part_country:
                    return True

    # Remote signals match any location - but only truly worldwide ones
    # "Remote in Europe" should NOT match "Tbilisi"
    if remote_in_loc:
        # Already handled above - geo-restricted remote, don't match here
        pass
    else:
        for signal in REMOTE_SIGNALS:
            if signal in job_loc:
                return True

    return False
