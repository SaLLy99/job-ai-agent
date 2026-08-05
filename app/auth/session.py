import requests

class SessionManager:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

    def set_cookies(self, cookies: dict):
        for k, v in cookies.items():
            self.session.cookies.set(k, v)

    def get(self, url):
        return self.session.get(url).text