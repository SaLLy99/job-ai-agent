import requests
import hashlib


class HimalayasCrawler:

    API_URL = "https://himalayas.app/jobs/api"

    def crawl(self, keywords=None):
        jobs = []

        search = ""
        if keywords:
            search = " ".join(keywords) if isinstance(keywords, list) else str(keywords)

        try:
            params = {"limit": 50, "offset": 0}
            if search:
                params["search"] = search

            r = requests.get(
                self.API_URL,
                params=params,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[himalayas] Error: {e}")
            return []

        for item in data.get("jobs", []):
            title = item.get("title", "").strip()
            company = item.get("companyName", "").strip()
            slug = item.get("companySlug", "")
            excerpt = item.get("excerpt", "")
            description = item.get("description", "")
            location_restrictions = item.get("locationRestrictions", [])
            timezone_restrictions = item.get("timezoneRestrictions", [])
            min_salary = item.get("minSalary")
            max_salary = item.get("maxSalary")
            salary_period = item.get("salaryPeriod", "")
            currency = item.get("currency", "")
            seniority = item.get("seniority", "")
            categories = item.get("categories", [])
            employment_type = item.get("employmentType", "")
            pub_date = item.get("pubDate", "")
            application_link = item.get("applicationLink", "")
            guid = item.get("guid", "")

            if not title:
                continue

            location = ", ".join(location_restrictions) if location_restrictions else "Worldwide"

            desc_text = description if description else excerpt

            url = application_link
            if not url:
                url = f"https://himalayas.app/jobs/{slug}" if slug else ""

            salary_info = ""
            if min_salary and max_salary:
                salary_info = f"{currency} {min_salary}-{max_salary} {salary_period}"
            elif min_salary:
                salary_info = f"{currency} {min_salary}+ {salary_period}"

            jobs.append({
                "id": hashlib.md5(f"himalayas:{guid or title}:{company}".encode()).hexdigest(),
                "title": title,
                "company": company,
                "url": url,
                "location": location,
                "description": (desc_text or "")[:2000],
                "source": "himalayas",
                "salary_min": salary_info,
                "tags": categories,
                "posted_date": pub_date,
                "seniority": seniority,
            })

        return jobs
