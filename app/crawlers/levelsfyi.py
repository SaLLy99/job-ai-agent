import requests
import hashlib
import json
from bs4 import BeautifulSoup


class LevelsFyiCrawler:

    BASE_URL = "https://www.levels.fyi/jobs"

    def crawl(self, keywords=None):
        jobs = []

        try:
            r = requests.get(
                self.BASE_URL,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"},
                timeout=15,
            )
            r.raise_for_status()
        except Exception as e:
            print(f"[levelsfyi] Error: {e}")
            return []

        soup = BeautifulSoup(r.text, "html.parser")

        for script in soup.select("script:not([src])"):
            text = script.text.strip()
            if "initialJobsData" not in text:
                continue
            try:
                data = json.loads(text)
            except (json.JSONDecodeError, ValueError):
                continue

            props = data.get("props", {}).get("pageProps", {})
            jobs_data = props.get("initialJobsData", {})
            results = jobs_data.get("results", [])

            for company in results:
                company_name = company.get("companyName", "")
                company_slug = company.get("companySlug", "")

                for j in company.get("jobs", []):
                    title = j.get("title", "").strip()
                    job_id = j.get("id", "")
                    locations = j.get("locations", [])
                    application_url = j.get("applicationUrl", "")
                    work_arrangement = j.get("workArrangement", "")
                    min_salary = j.get("minBaseSalary")
                    max_salary = j.get("maxBaseSalary")
                    salary_currency = j.get("baseSalaryCurrency", "")

                    if not title:
                        continue

                    if keywords:
                        search_text = f"{title} {company_name}".lower()
                        if not any(kw.lower() in search_text for kw in keywords if isinstance(kw, str)):
                            continue

                    location = ", ".join(locations) if locations else ""
                    salary_text = ""
                    if min_salary and max_salary:
                        salary_text = f"{salary_currency} {min_salary}-{max_salary}"
                    elif min_salary:
                        salary_text = f"{salary_currency} {min_salary}+"

                    url = application_url
                    if not url:
                        url = f"https://www.levels.fyi/companies/{company_slug}/jobs/{job_id}"

                    jobs.append({
                        "id": hashlib.md5(f"levels:{job_id or title}:{company_name}".encode()).hexdigest(),
                        "title": title,
                        "company": company_name,
                        "url": url,
                        "location": location,
                        "description": j.get("shortDescription", ""),
                        "source": "levels_fyi",
                        "salary_text": salary_text,
                        "tags": [work_arrangement] if work_arrangement else [],
                    })

            break

        return jobs
