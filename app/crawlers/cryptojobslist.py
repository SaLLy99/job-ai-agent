import requests
import hashlib
from bs4 import BeautifulSoup


class CryptoJobsListCrawler:

    BASE_URL = "https://cryptojobslist.com/remote"

    def crawl(self, keywords=None):
        jobs = []

        try:
            r = requests.get(
                self.BASE_URL,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
                timeout=15,
            )
            r.raise_for_status()
        except Exception as e:
            print(f"[cryptojobslist] Error: {e}")
            return []

        soup = BeautifulSoup(r.text, "html.parser")

        for link in soup.select("a[href*='/jobs/']"):
            href = link.get("href", "")
            title = link.text.strip()

            if not title or len(title) < 3:
                continue

            company = ""
            parts = href.rstrip("/").split("/")
            if len(parts) >= 2:
                slug = parts[-1]
                slug_parts = slug.split("-at-")
                if len(slug_parts) >= 2:
                    company = slug_parts[-1].replace("-", " ").title()
                else:
                    slug_parts = slug.rsplit("-", 2)
                    if len(slug_parts) >= 3:
                        company = slug_parts[-2].replace("-", " ").title()

            full_url = href if href.startswith("http") else f"https://cryptojobslist.com{href}"

            if keywords:
                text = f"{title} {company}".lower()
                if not any(k.lower() in text for k in keywords if isinstance(k, str)):
                    continue

            jobs.append({
                "id": hashlib.md5(f"cryptojobslist:{title}:{company}".encode()).hexdigest(),
                "title": title,
                "company": company,
                "url": full_url,
                "location": "Worldwide",
                "description": "",
                "source": "cryptojobslist",
            })

        return jobs
