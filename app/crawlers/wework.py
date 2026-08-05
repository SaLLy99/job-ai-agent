import requests, hashlib
from bs4 import BeautifulSoup

class WeWorkRemotelyCrawler:

    def crawl(self, keywords=None):
        try:
            r = requests.get(
                "https://weworkremotely.com/remote-jobs",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15
            )
            r.raise_for_status()
        except Exception as e:
            print(f"[wwr] Error: {e}")
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        jobs = []

        for li in soup.select("section.jobs li"):
            a = li.find("a")
            if not a:
                continue

            text = li.text.strip()

            jobs.append({
                "id": hashlib.md5(text.encode()).hexdigest(),
                "title": text[:120],
                "company": "",
                "url": "https://weworkremotely.com" + a["href"],
                "source": "wwr"
            })

        return jobs
