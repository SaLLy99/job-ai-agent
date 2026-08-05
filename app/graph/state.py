from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):

    # =========================================
    # USER INPUT
    # =========================================

    user_id: str

    query: str

    # =========================================
    # PARSED QUERY
    # =========================================

    parsed_query: Dict[str, Any]

    # =========================================
    # USER PROFILE
    # =========================================

    user_profile: Dict[str, Any]

    # =========================================
    # SCRAPED RAW JOBS
    # =========================================

    scraped_jobs: List[Dict[str, Any]]

    # =========================================
    # VALIDATED JOBS
    # =========================================

    validated_jobs: List[Dict[str, Any]]

    # =========================================
    # ENRICHED JOBS
    # =========================================

    enriched_jobs: List[Dict[str, Any]]

    # =========================================
    # DEDUPLICATED JOBS
    # =========================================

    jobs: List[Dict[str, Any]]

    # =========================================
    # FILTERED JOBS
    # =========================================

    filtered_jobs: List[Dict[str, Any]]

    # =========================================
    # RANKED JOBS
    # =========================================

    ranked_jobs: List[Dict[str, Any]]

    # =========================================
    # VERIFIED JOBS
    # =========================================

    verified_jobs: List[Dict[str, Any]]

    # =========================================
    # FINAL RESPONSE
    # =========================================

    final_response: str

    # =========================================
    # ERRORS
    # =========================================

    errors: List[str]

    # =========================================
    # CRAWLER STATS
    # =========================================

    crawler_stats: Dict[str, Any]

    # =========================================
    # REJECTION LOG
    # =========================================

    rejection_log: List[Dict[str, Any]]

    # =========================================
    # SESSION COOKIES (for authenticated crawlers)
    # =========================================

    session_cookies: Dict[str, str]
