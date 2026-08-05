import requests
import hashlib
from bs4 import BeautifulSoup


class RemoteIOCrawler:

    BASE_URL = "https://www.remote.io/jobs/"
    MAX_PAGES = 10

    def crawl(self, keywords=None):
        jobs = []
        seen_urls = set()

        for page in range(1, self.MAX_PAGES + 1):
            url = f"{self.BASE_URL}?page={page}" if page > 1 else self.BASE_URL

            try:
                r = requests.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml",
                    },
                    timeout=15,
                )
                r.raise_for_status()
            except Exception as e:
                print(f"[remoteio] Error page {page}: {e}")
                break

            soup = BeautifulSoup(r.text, "html.parser")

            page_links = []
            for link in soup.select("a[href*='/remote-jobs/']"):
                href = link.get("href", "")
                title = link.text.strip()

                if not title or len(title) < 3:
                    continue

                full_url = href if href.startswith("http") else f"https://www.remote.io{href}"

                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                company = ""
                parent = link.parent
                if parent:
                    siblings = parent.find_all(string=True, recursive=False)
                    for sib in siblings:
                        text = sib.strip()
                        if text and text != title and len(text) > 2 and len(text) < 80:
                            company = text
                            break

                if not company:
                    gp = link.parent.parent if link.parent else None
                    if gp:
                        all_text = gp.get_text(separator="|", strip=True)
                        parts = [p.strip() for p in all_text.split("|") if p.strip()]
                        title_idx = -1
                        for i, p in enumerate(parts):
                            if title in p:
                                title_idx = i
                                break
                        if title_idx >= 0 and title_idx + 1 < len(parts):
                            candidate = parts[title_idx + 1]
                            if len(candidate) < 80 and candidate != title:
                                company = candidate

                if keywords:
                    text = f"{title} {company}".lower()
                    if not any(k.lower() in text for k in keywords if isinstance(k, str)):
                        continue

                page_links.append({
                    "id": hashlib.md5(f"remoteio:{title}:{company}".encode()).hexdigest(),
                    "title": title,
                    "company": company,
                    "url": full_url,
                    "location": "Worldwide",
                    "description": "",
                    "source": "remoteio",
                })

            if not page_links and page > 1:
                break

            jobs.extend(page_links)

        return jobs
