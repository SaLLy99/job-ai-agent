from graph.state import AgentState
from agent.ranker import Ranker

def rank_jobs(state: AgentState):
    ranker = Ranker()
    profile = state.get('user_profile') or {"cv": {}, "prefs": {}}
    jobs = state.get('filtered_jobs') or state.get('jobs') or []
    query = state.get('query', '')
    parsed_query = state.get('parsed_query') or {}

    print(f"[RANK DEBUG] Input jobs: {len(jobs)}, query: {query}")

    try:
        ranked = ranker.rank(profile, jobs, query, parsed_query)
        state['ranked_jobs'] = ranked['results']
        print(f"[RANK DEBUG] Output: {len(ranked['results'])} ranked jobs")
    except Exception as e:
        print(f"[RANK DEBUG] ERROR: {e}")
        import traceback
        traceback.print_exc()
        state['errors'].append(f"Ranking failed: {e}")
        state['ranked_jobs'] = []

    return state
