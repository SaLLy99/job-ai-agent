import requests
import hashlib
from bs4 import BeautifulSoup

class RemoteRocketshipCrawler:

    BASE_URL = "https://www.remoterocketship.com"

    def crawl(self, keywords=None):
        params = {
            "page": 1,
            "sort": "DateAdded",
            "locations": "Worldwide",
        }
        if keywords:
            kw = keywords[0] if isinstance(keywords, list) and keywords else str(keywords)
            params["jobTitle"] = kw
        else:
            params["jobTitle"] = "Software Engineer"

        try:
            r = requests.get(
                self.BASE_URL,
                params=params,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15
            )
            r.raise_for_status()
        except Exception as e:
            print(f"[remoterocketship] Error: {e}")
            return []

        soup = BeautifulSoup(r.text, "html.parser")

        jobs = []

        for a in soup.select("a"):

            href = a.get("href", "")
            text = a.text.strip()

            if "/jobs/" not in href:
                continue

            if len(text) < 5:
                continue

            full_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

            jobs.append({
                "id": hashlib.md5(text.encode()).hexdigest(),
                "title": text,
                "company": "",
                "url": full_url,
                "source": "remoterocketship"
            })

        return jobs
