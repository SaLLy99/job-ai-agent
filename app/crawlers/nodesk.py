import requests
import hashlib
from bs4 import BeautifulSoup

class NodeSkCrawler:

    BASE_URL = "https://nodesk.co/remote-jobs/"

    def crawl(self, keywords=None):

        try:
            r = requests.get(
                self.BASE_URL,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15
            )
            r.raise_for_status()
        except Exception as e:
            print(f"[nodesk] Error: {e}")
            return []

        soup = BeautifulSoup(r.text, "html.parser")

        jobs = []

        for a in soup.select("a"):

            href = a.get("href", "")
            title = a.text.strip()

            if "/remote-jobs/" not in href:
                continue

            if len(title) < 5:
                continue

            jobs.append({
                "id": hashlib.md5(title.encode()).hexdigest(),
                "title": title,
                "company": "",
                "url": href,
                "source": "nodesk"
            })

        return jobs
