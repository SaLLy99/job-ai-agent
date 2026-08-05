import requests
import hashlib


class ArbeitnowCrawler:

    API_URL = "https://www.arbeitnow.com/api/job-board-api"

    def crawl(self, keywords=None):
        jobs = []
        page = 1

        while page <= 5:
            try:
                r = requests.get(
                    self.API_URL,
                    params={"page": page},
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=15,
                )
                data = r.json()
            except Exception:
                break

            job_list = data.get("data", [])
            if not job_list:
                break

            for item in job_list:
                title = item.get("title", "").strip()
                company = item.get("company_name", "").strip()
                url = item.get("url", "")
                location = item.get("location", "")
                description = item.get("description", "")
                remote = item.get("remote", False)
                tags = item.get("tags", [])
                posted_date = item.get("created_at", "")

                if not title:
                    continue

                if keywords:
                    text = f"{title} {description} {' '.join(tags)}".lower()
                    if not any(kw.lower() in text for kw in keywords if isinstance(kw, str)):
                        continue

                jobs.append({
                    "id": hashlib.md5(f"arbeitnow:{title}:{company}".encode()).hexdigest(),
                    "title": title,
                    "company": company,
                    "url": url,
                    "location": location,
                    "description": description,
                    "source": "arbeitnow",
                    "remote": remote,
                    "tags": tags,
                    "posted_date": posted_date,
                })

            if not data.get("links", {}).get("next"):
                break
            page += 1

        return jobs
