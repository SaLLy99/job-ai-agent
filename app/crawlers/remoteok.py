import requests, hashlib


class RemoteOKCrawler:

    API_URL = "https://remoteok.com/api"

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
            print(f"[remoteok] Error: {e}")
            return []

        if not isinstance(data, list) or len(data) < 2:
            return []

        jobs_raw = data[1:]

        if keywords:
            kw_set = [k.lower() for k in keywords if isinstance(k, str)]
            filtered = []
            for j in jobs_raw:
                text = f"{j.get('position', '')} {j.get('description', '')} {' '.join(j.get('tags', []))}".lower()
                if any(k in text for k in kw_set):
                    filtered.append(j)
            jobs_raw = filtered

        jobs = []
        for item in jobs_raw:
            title = item.get("position", "").strip()
            company = item.get("company", "").strip()
            url = item.get("url", "")
            location = item.get("location", "")
            description = item.get("description", "")[:2000]
            tags = item.get("tags", [])
            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")

            if not title:
                continue

            job = {
                "id": hashlib.md5(f"remoteok:{title}:{company}".encode()).hexdigest(),
                "title": title,
                "company": company,
                "url": url,
                "location": location or "Worldwide",
                "description": description,
                "source": "remoteok",
                "tags": tags,
            }
            if salary_min:
                job["salary_min"] = salary_min
            if salary_max:
                job["salary_max"] = salary_max

            jobs.append(job)

        return jobs
