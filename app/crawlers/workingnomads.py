import requests
import hashlib


class WorkingNomadsCrawler:

    API_URL = "https://www.workingnomads.com/api/exposed_jobs"

    def crawl(self, keywords=None):
        try:
            r = requests.get(
                self.API_URL,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[workingnomads] Error: {e}")
            return []

        if not isinstance(data, list):
            return []

        jobs = []
        for item in data:
            title = item.get("title", "").strip()
            company = item.get("company_name", "").strip()
            url = item.get("url", "") or item.get("link", "")
            location = item.get("location", "")
            description = item.get("description", "")[:2000]
            tags = item.get("tags", [])

            if not title:
                continue

            if keywords:
                text = f"{title} {description} {' '.join(tags) if isinstance(tags, list) else ''}".lower()
                if not any(k.lower() in text for k in keywords if isinstance(k, str)):
                    continue

            jobs.append({
                "id": hashlib.md5(f"workingnomads:{title}:{company}".encode()).hexdigest(),
                "title": title,
                "company": company,
                "url": url,
                "location": location,
                "description": description,
                "source": "workingnomads",
                "tags": tags,
            })

        return jobs
