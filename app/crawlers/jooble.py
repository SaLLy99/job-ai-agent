import os
import hashlib
import requests
from bs4 import BeautifulSoup


class JoobleCrawler:

    API_URL = "https://jooble.org/api/"
    API_KEY = os.getenv("JOOBLE_API_KEY", "")

    def crawl(self, keywords=None, location=None):
        if not self.API_KEY:
            print("[jooble] No JOOBLE_API_KEY set, skipping")
            return []

        kw = ""
        if keywords:
            kw = keywords[0] if isinstance(keywords, list) and keywords else str(keywords)

        try:
            r = requests.post(
                f"{self.API_URL}{self.API_KEY}",
                json={
                    "keywords": kw or "remote",
                    "location": location or "",
                    "page": 1,
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[jooble] API Error: {e}")
            return []

        jobs = []
        for item in data.get("jobs", []):
            title = item.get("title", "").strip()
            company = item.get("company", "").strip()
            url = item.get("link", "")
            location = item.get("location", "")
            description = item.get("snippet", "")
            salary = item.get("salary", "")

            if not title:
                continue

            jobs.append({
                "id": hashlib.md5(f"jooble:{title}:{company}".encode()).hexdigest(),
                "title": title,
                "company": company,
                "url": url,
                "location": location,
                "description": description[:2000],
                "source": "jooble",
                "salary_text": salary,
            })

        return jobs
