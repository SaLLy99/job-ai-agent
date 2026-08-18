from .remoteok import RemoteOKCrawler
from .wework import WeWorkRemotelyCrawler
from .workingnomads import WorkingNomadsCrawler
from .nodesk import NodeSkCrawler
from .himalayas import HimalayasCrawler
from .remotehub import RemoteHubCrawler
from .remoterocketship import RemoteRocketshipCrawler
from .trulyremote import TrulyRemoteCrawler
from .workday import WorkwayCrawler
from .djinni import DjinniCrawler
from .linkedin import LinkedInCrawler
from .remotive import RemotiveCrawler
from .jobicy import JobicyCrawler
from .arbeitnow import ArbeitnowCrawler
from .builtin import BuiltinCrawler
from .levelsfyi import LevelsFyiCrawler
from .jooble import JoobleCrawler
from .hubstafftalent import HubstaffTalentCrawler
from .hiringcafe import HiringCafeCrawler
from .reed import ReedCrawler
from .remoteio import RemoteIOCrawler
from .cryptojobslist import CryptoJobsListCrawler
from .micro1 import Micro1Crawler

# Per-crawler limits: ensure balanced representation
PER_CRAWLER_MIN = 3
PER_CRAWLER_MAX = 15
TOTAL_TARGET = 150


class JobCrawlerManager:

    def __init__(self, session=None):

        self.crawlers = [
            LinkedInCrawler(),
            RemoteOKCrawler(),
            WeWorkRemotelyCrawler(),
            WorkingNomadsCrawler(),
            NodeSkCrawler(),
            HimalayasCrawler(),
            RemoteHubCrawler(),
            RemoteRocketshipCrawler(),
            TrulyRemoteCrawler(),
            WorkwayCrawler(),
            RemotiveCrawler(),
            JobicyCrawler(),
            ArbeitnowCrawler(),
            BuiltinCrawler(),
            LevelsFyiCrawler(),
            JoobleCrawler(),
            HubstaffTalentCrawler(),
            HiringCafeCrawler(),
            ReedCrawler(),
            RemoteIOCrawler(),
            CryptoJobsListCrawler(),
            Micro1Crawler(),
        ]

        self.session = session
        if self.session:
            raw_session = getattr(session, 'session', session)
            for crawler in self.crawlers:
                if isinstance(crawler, LinkedInCrawler):
                    crawler.session = raw_session
                    break
            self.crawlers.append(DjinniCrawler(self.session))

    def crawl_all(self, keywords=None, location=None):
        """Run all crawlers and balance results per source."""
        per_source = {}

        for crawler in self.crawlers:
            source = crawler.__class__.__name__
            try:
                # Try with both keywords and location
                result = crawler.crawl(keywords=keywords, location=location)
                if result is None:
                    result = []
            except TypeError:
                try:
                    # Try with keywords only
                    result = crawler.crawl(keywords=keywords)
                    if result is None:
                        result = []
                except TypeError:
                    try:
                        # Try with no arguments
                        result = crawler.crawl()
                        if result is None:
                            result = []
                    except Exception as e:
                        print(f"[CRAWL] {source} FAILED: {e}")
                        result = []
                except Exception as e:
                    print(f"[CRAWL] {source} FAILED: {e}")
                    result = []
            except Exception as e:
                print(f"[CRAWL] {source} FAILED: {e}")
                result = []

            print(f"[CRAWL] {source}: {len(result)} jobs")
            per_source[source] = result

        return self._balance_results(per_source)

    def _balance_results(self, per_source):
        """Balance results: min 3, max 15 per source, fill to target total."""
        active_sources = {s: self._deduplicate_list(j) for s, j in per_source.items() if j}
        n_sources = len(active_sources)

        if n_sources == 0:
            return []

        # Step 1: take min from each source
        balanced = []
        overflow = []
        for source, jobs in active_sources.items():
            if len(jobs) <= PER_CRAWLER_MIN:
                balanced.extend(jobs)
            else:
                balanced.extend(jobs[:PER_CRAWLER_MIN])
                overflow.extend(jobs[PER_CRAWLER_MIN:])

        # Step 2: calculate remaining slots and distribute overflow fairly
        remaining = TOTAL_TARGET - len(balanced)
        if remaining > 0 and overflow:
            # Group overflow by source
            overflow_by_source = {}
            for j in overflow:
                src = j.get("source", "unknown")
                overflow_by_source.setdefault(src, []).append(j)

            # Calculate fair share per source (capped at PER_CRAWLER_MAX total)
            per_source_total = {}
            for source, jobs in active_sources.items():
                per_source_total[source] = len(balanced)

            slots_per_source = max(1, remaining // max(1, len(overflow_by_source)))
            added = 0

            for source, jobs in overflow_by_source.items():
                current = per_source_total.get(source, 0)
                can_add = min(slots_per_source, PER_CRAWLER_MAX - current, remaining - added)
                if can_add > 0:
                    balanced.extend(jobs[:can_add])
                    added += can_add

        return self._deduplicate_list(balanced)

    def _deduplicate_list(self, jobs):
        """Deduplicate by title+company key."""
        seen = set()
        output = []
        for j in jobs:
            key = (j["title"].lower().strip() + j["company"].lower().strip())
            if key not in seen:
                seen.add(key)
                output.append(j)
        return output

    # Keep old method for backward compatibility
    def deduplicate(self, jobs):
        return self._deduplicate_list(jobs)
