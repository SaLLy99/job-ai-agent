import requests
import hashlib
from bs4 import BeautifulSoup


class HiringCafeCrawler:

    BASE_URL = "https://hiring.cafe/"

    def crawl(self):
        jobs = []
        try:
            r = requests.get(
                self.BASE_URL,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            soup = BeautifulSoup(r.text, "html.parser")

            for card in soup.select("a[href*='/positions/'], a[href*='/jobs/'], [class*='job-card'], [class*='listing']"):
                title_el = card.select_one("h2, h3, [class*='title']")
                company_el = card.select_one("[class*='company'], [class*='org']")
                location_el = card.select_one("[class*='location']")
                desc_el = card.select_one("[class*='description'], p")
                salary_el = card.select_one("[class*='salary'], [class*='comp']")

                if not title_el:
                    text = card.text.strip()
                    if len(text) < 5:
                        continue
                    title_text = text[:120]
                else:
                    title_text = title_el.text.strip()

                href = card.get("href", "")
                if href and not href.startswith("http"):
                    href = f"https://hiring.cafe{href}"

                jobs.append({
                    "id": hashlib.md5(f"hiringcafe:{title_text}:{company_el.text.strip() if company_el else ''}".encode()).hexdigest(),
                    "title": title_text,
                    "company": company_el.text.strip() if company_el else "",
                    "url": href,
                    "location": location_el.text.strip() if location_el else "",
                    "description": desc_el.text.strip() if desc_el else "",
                    "salary_text": salary_el.text.strip() if salary_el else "",
                    "source": "hiringcafe",
                })
        except Exception as e:
            print(f"[HiringCafeCrawler] Error: {e}")

        return jobs
