from typing import TypedDict, List, Dict, Optional

class AgentState(TypedDict):
    user_id: str
    query: str
    parsed_query: Dict
    scraped_jobs: List[Dict]
    ranked_jobs: List[Dict]
    final_response: str
    errors: List[str]
    user_profile: Dict