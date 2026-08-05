from ..state import AgentState

def deduplicate(state: AgentState):
    jobs = state.get('enriched_jobs', [])
    seen = set()
    output = []

    for j in jobs:
        key = (
            j["title"].lower().strip() +
            j["company"].lower().strip()
        )

        if key not in seen:
            seen.add(key)
            output.append(j)

    state['jobs'] = output
    print(f"[DEDUP DEBUG] Deduplicated: {len(jobs)} -> {len(output)} jobs")
    return state