import requests
import hashlib


class RemotiveCrawler:

    API_URL = "https://remotive.com/api/remote-jobs"

    def crawl(self, keywords=None):
        params = {}
        if keywords:
            tag_map = {
                "java": "software-dev",
                "python": "software-dev",
                "javascript": "software-dev",
                "typescript": "software-dev",
                "react": "software-dev",
                "node": "software-dev",
                "devops": "software-dev",
                "frontend": "software-dev",
                "backend": "software-dev",
                "fullstack": "software-dev",
                "full stack": "software-dev",
                "full-stack": "software-dev",
                "mobile": "software-dev",
                "flutter": "software-dev",
                "kotlin": "software-dev",
                "swift": "software-dev",
                "golang": "software-dev",
                "rust": "software-dev",
                "ruby": "software-dev",
                "php": "software-dev",
                "sql": "software-dev",
                "aws": "software-dev",
                "azure": "software-dev",
                "gcp": "software-dev",
                "docker": "software-dev",
                "kubernetes": "software-dev",
                "machine learning": "software-dev",
                "ai": "software-dev",
                "data science": "software-dev",
                "data engineer": "software-dev",
                "ux": "design",
                "ui": "design",
                "design": "design",
                "product": "product",
                "marketing": "marketing",
                "sales": "sales",
                "customer support": "customer-support",
                "accounting": "accounting",
                "finance": "accounting",
                "hr": "human-resources",
                "recruiting": "human-resources",
                "writing": "writing",
                "copywriting": "writing",
            }
            categories = set()
            for kw in keywords:
                if isinstance(kw, str):
                    cat = tag_map.get(kw.lower())
                    if cat:
                        categories.add(cat)
            if categories:
                params["category"] = ",".join(categories)

        try:
            r = requests.get(
                self.API_URL,
                params=params,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            data = r.json()
        except Exception:
            return []

        jobs = []
        for item in data.get("jobs", []):
            title = item.get("title", "").strip()
            company = item.get("company_name", "").strip()
            url = item.get("url", "")
            location = item.get("candidate_required_location", "")
            description = item.get("description", "")
            tags = item.get("tags", [])
            posted_date = item.get("publication_date", "")

            if not title:
                continue

            jobs.append({
                "id": hashlib.md5(f"remotive:{title}:{company}".encode()).hexdigest(),
                "title": title,
                "company": company,
                "url": url,
                "location": location,
                "description": description,
                "source": "remotive",
                "tags": tags,
                "posted_date": posted_date,
            })

        return jobs
