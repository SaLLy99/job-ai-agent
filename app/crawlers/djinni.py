import hashlib
from bs4 import BeautifulSoup

class DjinniCrawler:

    def __init__(self, session):
        self.session = session

    def crawl(self, keywords=None, location=None):
        html = self.session.get("https://djinni.co/jobs/")
        soup = BeautifulSoup(html, "html.parser")

        jobs = []

        for job in soup.select(".job-list-item"):
            title = job.select_one(".job-list-item__title")
            link = job.find("a")

            if not title:
                continue

            jobs.append({
                "id": hashlib.md5(title.text.encode()).hexdigest(),
                "title": title.text.strip(),
                "company": "",
                "url": "https://djinni.co" + link["href"],
                "source": "djinni"
            })

        return jobs