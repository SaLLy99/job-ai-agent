from crawlers.manager import JobCrawlerManager
from agent.ranker import Ranker
from agent.memory import Memory

class Controller:

    def __init__(self, session=None):
        self.memory = Memory()
        self.crawlers = JobCrawlerManager(session)
        self.ranker = Ranker()

    def run(self, user_id, query, cv=None, prefs=None):

        profile = self.memory.get_profile(user_id)

        if cv:
            profile = {"cv": cv, "prefs": prefs}
            self.memory.save_profile(user_id, cv, prefs)

        jobs = self.crawlers.crawl_all()

        ranked = self.ranker.rank(profile, jobs, query)

        self.memory.save_chat(user_id, query, ranked)

        return ranked