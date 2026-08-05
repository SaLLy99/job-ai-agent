import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from graph.state import AgentState

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
TIMEOUT = 8
MAX_WORKERS = 8


def _fetch_description(url):
    """Fetch and extract text description from a job URL."""
    if not url:
        return ""
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        for selector in [
            "article",
            "[class*='job-description']",
            "[class*='job-description']",
            "[class*='description']",
            "[data-testid='job-description']",
            "main",
            ".content",
        ]:
            el = soup.select_one(selector)
            if el and len(el.get_text(strip=True)) > 50:
                return el.get_text(separator="\n", strip=True)[:3000]

        body = soup.find("body")
        if body:
            return body.get_text(separator="\n", strip=True)[:2000]
    except Exception:
        pass
    return ""


def enrich_jobs(state: AgentState):
    jobs = state.get("validated_jobs", state.get("scraped_jobs", []))

    needs_enrichment = [j for j in jobs if not j.get("description")]
    already_have = [j for j in jobs if j.get("description")]

    print(f"[ENRICH] {len(needs_enrichment)} jobs need description, {len(already_have)} already have one")

    if needs_enrichment:
        urls = [j.get("url", "") for j in needs_enrichment]
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(_fetch_description, url): i for i, url in enumerate(urls)}
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    desc = future.result()
                    if desc:
                        needs_enrichment[idx]["description"] = desc
                except Exception:
                    pass

        enriched_count = sum(1 for j in needs_enrichment if j.get("description"))
        print(f"[ENRICH] Successfully enriched {enriched_count}/{len(needs_enrichment)} jobs")

    state["enriched_jobs"] = jobs
    return state
