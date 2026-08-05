import requests
import hashlib
from bs4 import BeautifulSoup


class WorkwayCrawler:

    BASE_URL = "https://www.workway.dev"

    def crawl(self, keywords=None):
        try:
            r = requests.get(
                f"{self.BASE_URL}/jobs",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                },
                timeout=15,
            )
            r.raise_for_status()
        except Exception as e:
            print(f"[workway] Error: {e}")
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        jobs = []

        for a in soup.select("a[href*='/jobs/'], a[href*='/job/']"):
            href = a.get("href", "")
            title = a.text.strip()

            if "/jobs/new" in href or len(title) < 5:
                continue

            full_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

            company = ""
            parent = a.parent
            if parent:
                text_parts = parent.get_text(separator="|", strip=True).split("|")
                for part in text_parts:
                    if part.strip() != title and len(part.strip()) > 2 and len(part.strip()) < 60:
                        company = part.strip()
                        break

            if keywords:
                search_text = f"{title} {company}".lower()
                if not any(k.lower() in search_text for k in keywords if isinstance(k, str)):
                    continue

            jobs.append({
                "id": hashlib.md5(f"workway:{title}:{company}".encode()).hexdigest(),
                "title": title,
                "company": company,
                "url": full_url,
                "location": "Worldwide",
                "description": "",
                "source": "workway",
            })

        return jobs
