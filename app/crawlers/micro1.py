import requests
import hashlib


class Micro1Crawler:

    BASE_URL = "https://www.micro1.ai"
    API_URL = "https://prod-api.micro1.ai/api/v1/job/portal"
    OPPORTUNITIES_URL = "https://www.micro1.ai/experts/opportunities"

    def crawl(self, keywords=None):
        jobs = []

        try:
            params = {
                "page": 1,
                "limit": 50,
                "keyword": " ".join(keywords) if keywords else "",
            }

            r = requests.post(
                self.API_URL,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Content-Type": "application/json",
                },
                json={
                    "action": "get_all_jobs",
                    "filters": {"type": ["EXPERT"]},
                },
                params=params,
                timeout=15,
            )
            r.raise_for_status()
        except Exception as e:
            print(f"[micro1] Error: {e}")
            return []

        data = r.json()
        job_list = data.get("data", [])

        for job in job_list:
            title = job.get("job_name", "")
            if not title:
                continue

            company = job.get("company_name") or "micro1"
            url = job.get("url") or self.OPPORTUNITIES_URL
            location = job.get("location") or "Worldwide"
            description = job.get("description") or ""
            job_type = job.get("type") or ""

            skills = job.get("skills") or []
            if skills:
                description += "\n\nSkills: " + ", ".join(skills)

            salary_min = job.get("salary_min")
            salary_max = job.get("salary_max")
            if salary_min and salary_max:
                description += f"\n\nSalary: ${salary_min:,} - ${salary_max:,} USD"

            jobs.append({
                "id": hashlib.md5(f"micro1:{title}:{company}".encode()).hexdigest(),
                "title": title,
                "company": company,
                "url": url,
                "location": location,
                "description": description[:2000],
                "source": "micro1",
            })

        return jobs
