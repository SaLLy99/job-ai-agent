from graph.state import AgentState
from db.repository import Repository

def save_memory(state: AgentState):
    repo = Repository()
    user_id = state.get('user_id')
    if not user_id:
        state['errors'].append('Missing user_id in state for save_memory')
        return state

    repo.save_chat(
        user_id=user_id,
        msg=state.get('query', ''),
        resp=state.get('verified_jobs', state.get('ranked_jobs', []))
    )
    return state
