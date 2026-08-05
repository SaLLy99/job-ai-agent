import hashlib
import requests
import json
from bs4 import BeautifulSoup


class LinkedInCrawler:
    """
    LinkedIn job crawler supporting two modes:
    - Authenticated: Uses session cookies for Voyager API (rich data, salary, descriptions)
    - Unauthenticated: Uses public HTML scraping (basic data from job search pages)
    """

    SEARCH_URL = "https://www.linkedin.com/jobs/search/"
    VOYAGER_API = "https://www.linkedin.com/voyager/api/voyagerJobsDashJobSearch"
    VIEW_URL = "https://www.linkedin.com/jobs/view/"

    def __init__(self, session=None):
        self.session = session
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def crawl(self, keywords=None, location=None):
        if self.session:
            jobs = self._crawl_authenticated(keywords, location)
            if jobs:
                return jobs
            print("[linkedin] Authenticated crawl failed, falling back to HTML scraping")

        return self._crawl_public(keywords, location)

    def _crawl_authenticated(self, keywords=None, location=None):
        """Use LinkedIn's Voyager API with session cookies for rich data."""
        try:
            search_term = " ".join(keywords) if keywords else ""
            params = {
                "decorationId": "com.linkedin.voyager.dash.decoserpserp.job-search.JobSearchResultCollection-36",
                "q": "all",
                "keywords": search_term,
                "start": 0,
                "count": 25,
                "f_TPR": "r604800",  # Last week
                "sortBy": "DD",  # Date descending
            }
            if location:
                params["location"] = location

            api_headers = self.headers.copy()
            api_headers["Accept"] = "application/json"
            api_headers["x-restli-protocol-version"] = "2.0.0"

            r = self.session.get(
                self.VOYAGER_API,
                params=params,
                headers=api_headers,
                timeout=15,
            )
            if r.status_code != 200:
                print(f"[linkedin] Voyager API returned {r.status_code}")
                return []

            data = r.json()
            jobs = []
            results = data.get("elements", [])

            for item in results:
                job_data = item.get("jobResult", item)
                if not job_data:
                    continue

                title = job_data.get("title", "").strip()
                company = job_data.get("companyName", "").strip()
                if not title:
                    continue

                job_id = job_data.get("entityUrn", "")
                if not job_id:
                    job_id = f"{title}:{company}"
                job_id = job_id.split(":")[-1]

                url = job_data.get("jobPostingUrl", "")
                if not url and job_id:
                    url = f"{self.VIEW_URL}{job_id}"
                elif url and not url.startswith("http"):
                    url = f"https://www.linkedin.com{url}"

                location = job_data.get("formattedLocation", "Worldwide")
                description = job_data.get("description", "")
                if not description:
                    description = job_data.get("summary", "")

                salary_info = job_data.get("salaryInsights", {})
                salary_min = None
                salary_max = None
                if salary_info:
                    salary_min = salary_info.get("minSalary")
                    salary_max = salary_info.get("maxSalary")

                job_type = job_data.get("employmentType", "")
                seniority = job_data.get("seniorityLevel", "")
                posted = job_data.get("listedAt", "")

                tags = []
                if seniority:
                    tags.append(seniority)
                if job_type:
                    tags.append(job_type)
                for skill in job_data.get("skills", []):
                    if isinstance(skill, dict):
                        tags.append(skill.get("name", ""))
                    elif isinstance(skill, str):
                        tags.append(skill)

                job = {
                    "id": hashlib.md5(f"linkedin:{title}:{company}".encode()).hexdigest(),
                    "title": title,
                    "company": company,
                    "url": url,
                    "location": location or "Worldwide",
                    "description": (description or "")[:2000],
                    "source": "linkedin",
                    "tags": [t for t in tags if t],
                }
                if salary_min:
                    job["salary_min"] = salary_min
                if salary_max:
                    job["salary_max"] = salary_max
                if job_type:
                    job["job_type"] = job_type
                if posted:
                    job["posted_date"] = posted
                if seniority:
                    job["seniority"] = seniority

                jobs.append(job)

            return jobs

        except Exception as e:
            print(f"[linkedin] Authenticated crawl error: {e}")
            return []

    def _crawl_public(self, keywords=None, location=None):
        """Scrape LinkedIn's public job search pages (no auth required)."""
        jobs = []
        try:
            search_term = " ".join(keywords) if keywords else ""
            params = {
                "keywords": search_term,
                "f_TPR": "r604800",  # Last week
                "sortBy": "DD",
                "position": 1,
                "pageNum": 0,
            }
            if location:
                params["location"] = location

            r = requests.get(
                self.SEARCH_URL,
                params=params,
                headers=self.headers,
                timeout=15,
            )
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            cards = soup.select("li")
            for card in cards:
                link = card.select_one("a[href*='/jobs/view/']")
                if not link:
                    link = card.select_one("a[data-tracking-control-name='public_jobs_jserp-result']")

                if not link:
                    continue

                title_el = card.select_one("h3") or card.select_one(".base-search-card__title")
                if not title_el:
                    title_el = link

                title = title_el.text.strip() if title_el else ""
                if not title or len(title) < 3:
                    continue

                company_el = card.select_one(".base-search-card__subtitle") or card.select_one("h4")
                company = company_el.text.strip() if company_el else ""
                company = company.replace("·", "").strip()

                location_el = card.select_one(".job-search-card__location")
                location = location_el.text.strip() if location_el else "Worldwide"

                href = link.get("href", "")
                if not href:
                    continue
                url = href.split("?")[0]
                if not url.startswith("http"):
                    url = f"https://www.linkedin.com{url}"

                time_el = card.select_one("time")
                posted = ""
                if time_el:
                    posted = time_el.get("datetime", "") or time_el.text.strip()

                jobs.append({
                    "id": hashlib.md5(f"linkedin:{title}:{company}".encode()).hexdigest(),
                    "title": title,
                    "company": company,
                    "url": url,
                    "location": location,
                    "source": "linkedin",
                    "posted_date": posted,
                })

            # Paginate: try pages 2 and 3
            if len(jobs) > 0:
                for page in [25, 50]:
                    params["start"] = page
                    try:
                        r2 = requests.get(
                            self.SEARCH_URL,
                            params=params,
                            headers=self.headers,
                            timeout=15,
                        )
                        if r2.status_code != 200:
                            continue
                        soup2 = BeautifulSoup(r2.text, "html.parser")
                        for card in soup2.select("li"):
                            link = card.select_one("a[href*='/jobs/view/']")
                            if not link:
                                link = card.select_one("a[data-tracking-control-name='public_jobs_jserp-result']")
                            if not link:
                                continue

                            title_el = card.select_one("h3") or card.select_one(".base-search-card__title")
                            if not title_el:
                                title_el = link
                            title = title_el.text.strip() if title_el else ""
                            if not title or len(title) < 3:
                                continue

                            company_el = card.select_one(".base-search-card__subtitle") or card.select_one("h4")
                            company = company_el.text.strip() if company_el else ""
                            company = company.replace("·", "").strip()

                            location_el = card.select_one(".job-search-card__location")
                            location = location_el.text.strip() if location_el else "Worldwide"

                            href = link.get("href", "")
                            if not href:
                                continue
                            url = href.split("?")[0]
                            if not url.startswith("http"):
                                url = f"https://www.linkedin.com{url}"

                            jobs.append({
                                "id": hashlib.md5(f"linkedin:{title}:{company}".encode()).hexdigest(),
                                "title": title,
                                "company": company,
                                "url": url,
                                "location": location,
                                "source": "linkedin",
                            })
                    except Exception:
                        continue

        except Exception as e:
            print(f"[linkedin] Public scrape error: {e}")

        return jobs
