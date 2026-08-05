import requests

class BaseCrawler:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.timeout = 10

    def crawl(self, keywords=None, location=None):
        raise NotImplementedError

    def get_details(self, url):
        return "" # Default empty if not implemented
