import requests
import hashlib


class JobicyCrawler:

    API_URL = "https://jobicy.com/api/v2/remote-jobs"

    def crawl(self, keywords=None):
        jobs = []

        try:
            r = requests.get(
                self.API_URL,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            data = r.json()
        except Exception as e:
            print(f"[jobicy] Error: {e}")
            return []

        job_list = data.get("jobs", [])

        for item in job_list:
            title = item.get("jobTitle", "").strip()
            company = item.get("companyName", "").strip()
            url = item.get("url", "")
            location = item.get("jobGeo", "")
            description = item.get("jobDescription", "")
            job_type = item.get("jobType", [])
            salary_min = item.get("annualSalaryMin", "")
            posted_date = item.get("pubDate", "")

            if not title:
                continue

            if keywords:
                text = f"{title} {description}".lower()
                if not any(k.lower() in text for k in keywords if isinstance(k, str)):
                    continue

            jobs.append({
                "id": hashlib.md5(f"jobicy:{title}:{company}".encode()).hexdigest(),
                "title": title,
                "company": company,
                "url": url,
                "location": location or "Worldwide",
                "description": description[:2000],
                "source": "jobicy",
                "salary_min": salary_min,
                "job_type": job_type,
                "posted_date": posted_date,
            })

        return jobs
