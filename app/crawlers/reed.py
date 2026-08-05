import requests
import hashlib
import json
from bs4 import BeautifulSoup


class ReedCrawler:

    BASE_URL = "https://www.reed.co.uk/jobs"

    def crawl(self, keywords=None):
        jobs = []

        query = "remote"
        if keywords:
            query = "+".join(keywords) if isinstance(keywords, list) else str(keywords)

        url = f"{self.BASE_URL}/{query}?remote=true"

        try:
            r = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            r.raise_for_status()
        except Exception as e:
            print(f"[reed] Error: {e}")
            return []

        soup = BeautifulSoup(r.text, "html.parser")

        for script in soup.select("script:not([src])"):
            text = script.text.strip()
            if "pageProps" not in text or len(text) < 500:
                continue
            try:
                data = json.loads(text)
            except (json.JSONDecodeError, ValueError):
                continue

            props = data.get("props", {}).get("pageProps", {})
            search_results = props.get("searchResults", {})
            job_list = search_results.get("jobs", [])

            for entry in job_list:
                detail = entry.get("jobDetail", {})
                if not detail:
                    continue

                title = detail.get("jobTitle", "").strip()
                company = detail.get("ouName", "")
                location = detail.get("displayLocationName", "")
                description = detail.get("jobDescriptionSnippet", "")
                job_id = detail.get("jobId", "")
                salary_from = detail.get("salaryFrom")
                salary_to = detail.get("salaryTo")
                salary_currency = detail.get("salaryCurrencyId")
                date_created = detail.get("dateCreated", "")
                is_full_time = detail.get("isFullTime", False)
                is_part_time = detail.get("isPartTime", False)
                job_url = entry.get("url", "")
                ou_url = entry.get("ouUrl", "")

                if not title:
                    continue

                if not job_url and job_id:
                    job_url = f"https://www.reed.co.uk/jobs/{job_url or job_id}"

                contract_type = ""
                if is_full_time:
                    contract_type = "Full-time"
                elif is_part_time:
                    contract_type = "Part-time"

                salary_str = ""
                if salary_from and salary_to:
                    salary_str = f"{salary_from}-{salary_to}"
                elif salary_from:
                    salary_str = f"{salary_from}+"

                location = location or "UK"

                jobs.append({
                    "id": hashlib.md5(f"reed:{job_id or title}:{company}".encode()).hexdigest(),
                    "title": title,
                    "company": company,
                    "url": f"https://www.reed.co.uk{job_url}" if job_url and not job_url.startswith("http") else job_url,
                    "location": location,
                    "description": description[:2000],
                    "source": "reed",
                    "salary_min": salary_str,
                    "tags": [contract_type] if contract_type else [],
                    "posted_date": date_created,
                })

            break

        return jobs
