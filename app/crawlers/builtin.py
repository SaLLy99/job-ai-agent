import requests
import hashlib
from bs4 import BeautifulSoup


class BuiltinCrawler:

    BASE_URL = "https://builtin.com/jobs/remote"

    def crawl(self, keywords=None):
        jobs = []
        try:
            url = self.BASE_URL
            if keywords:
                kw = keywords[0] if isinstance(keywords, list) and keywords else str(keywords)
                url = f"https://builtin.com/jobs/remote?search={kw}"

            r = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            seen = set()
            for a in soup.select("a"):
                href = a.get("href", "")
                if "/jobs/" not in href or href == "/jobs/remote":
                    continue
                if "?" in href and "page=" in href:
                    continue

                text = a.text.strip()
                if len(text) < 5 or len(text) > 200:
                    continue

                full_url = href if href.startswith("http") else f"https://builtin.com{href}"

                if full_url in seen:
                    continue
                seen.add(full_url)

                jobs.append({
                    "id": hashlib.md5(f"builtin:{text}:{full_url}".encode()).hexdigest(),
                    "title": text[:120],
                    "company": "",
                    "url": full_url,
                    "source": "builtin",
                })

        except Exception as e:
            print(f"[builtin] Error: {e}")

        return jobs
