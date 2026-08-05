import json
from db.sqlite import get_conn, init_db

class Repository:
    def get_profile(self, user_id: str):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT cv, prefs, identity FROM profile WHERE user_id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        if not row: return {"cv": {}, "prefs": {}, "identity": {}}
        cv = json.loads(row[0]) if row[0] else {}
        prefs = json.loads(row[1]) if row[1] else {}
        identity = json.loads(row[2]) if row[2] else {}
        if not isinstance(cv, dict): cv = {}
        if not isinstance(prefs, dict): prefs = {}
        if not isinstance(identity, dict): identity = {}
        return {"cv": cv, "prefs": prefs, "identity": identity}

    def save_profile(self, user_id, cv, prefs, identity=None):
        conn = get_conn()
        c = conn.cursor()
        identity_json = json.dumps(identity) if identity else "{}"
        c.execute("""
            INSERT INTO profile (user_id, cv, prefs, identity) VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET cv=excluded.cv, prefs=excluded.prefs, identity=excluded.identity
        """, (user_id, json.dumps(cv), json.dumps(prefs), identity_json))
        conn.commit()
        conn.close()

    def save_chat(self, user_id, msg, resp):
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO chat (user_id, msg, resp) VALUES (?, ?, ?)",
                  (user_id, msg, json.dumps(resp)))
        conn.commit()
        conn.close()

    def save_crawler_stats(self, crawler_name, total, validated, rejected):
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            INSERT INTO crawler_stats (crawler_name, total, validated, rejected)
            VALUES (?, ?, ?, ?)
        """, (crawler_name, total, validated, rejected))
        conn.commit()
        conn.close()

    def get_crawler_stats(self):
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT crawler_name,
                   SUM(total) as total,
                   SUM(validated) as validated,
                   SUM(rejected) as rejected
            FROM crawler_stats
            GROUP BY crawler_name
            ORDER BY total DESC
        """)
        rows = c.fetchall()
        conn.close()
        return [
            {"crawler": r[0], "total": r[1], "validated": r[2], "rejected": r[3]}
            for r in rows
        ]

    def save_batch_crawler_stats(self, crawler_stats):
        for crawler_name, stats in crawler_stats.items():
            self.save_crawler_stats(
                crawler_name,
                stats.get("total", 0),
                stats.get("validated", 0),
                stats.get("rejected", 0),
            )
