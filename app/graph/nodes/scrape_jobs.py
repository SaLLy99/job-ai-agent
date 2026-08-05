from crawlers.manager import JobCrawlerManager
from graph.state import AgentState
from auth.session import SessionManager


def scrape_jobs(state: AgentState):
    parsed = state.get("parsed_query", {})
    keywords = parsed.get("keywords", [])
    location = parsed.get("location", "")

    session = None
    cookies = state.get("session_cookies", {})
    if cookies:
        try:
            session = SessionManager()
            session.set_cookies(cookies)
        except Exception:
            pass

    manager = JobCrawlerManager(session=session)
    state['scraped_jobs'] = manager.crawl_all(keywords=keywords, location=location)
    print(f"[SCRAPE DEBUG] Scraped {len(state['scraped_jobs'])} jobs (keywords={keywords}, location={location})")
    return state
