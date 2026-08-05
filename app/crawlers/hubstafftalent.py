import requests
import hashlib
from bs4 import BeautifulSoup


class HubstaffTalentCrawler:

    SEARCH_URL = "https://hubstafftalent.net/search/jobs"

    def crawl(self, keywords=None):
        jobs = []

        url = self.SEARCH_URL
        if keywords:
            kw = keywords[0] if isinstance(keywords, list) and keywords else str(keywords)
            url = f"{self.SEARCH_URL}?search%5Bkeyword%5D={kw}"

        try:
            r = requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                },
                timeout=15,
            )
            r.raise_for_status()
        except Exception as e:
            print(f"[hubstafftalent] Error: {e}")
            return []

        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.select("a[href*='/jobs/']"):
            href = a.get("href", "")
            title = a.text.strip()

            if "/jobs/new" in href or "/jobs/" not in href:
                continue

            if len(title) < 5:
                continue

            full_url = href if href.startswith("http") else f"https://hubstafftalent.net{href}"

            company = ""
            parent = a.parent
            if parent:
                company_el = parent.select_one("[class*='company'], [class*='employer']")
                if company_el:
                    company = company_el.text.strip()

            if keywords:
                search_text = f"{title} {company}".lower()
                if not any(k.lower() in search_text for k in keywords if isinstance(k, str)):
                    continue

            jobs.append({
                "id": hashlib.md5(f"hubstaff:{title}:{company}".encode()).hexdigest(),
                "title": title,
                "company": company,
                "url": full_url,
                "location": "Worldwide",
                "description": "",
                "source": "hubstafftalent",
            })

        return jobs
