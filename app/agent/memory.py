import json
from db.sqlite import get_conn

class Memory:

    def get_profile(self, user_id):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT cv, prefs FROM profile WHERE user_id=?", (user_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "cv": json.loads(row[0]),
            "prefs": json.loads(row[1])
        }

    def save_profile(self, user_id, cv, prefs):
        conn = get_conn()
        c = conn.cursor()

        c.execute("""
        INSERT INTO profile (user_id, cv, prefs)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
        cv=excluded.cv,
        prefs=excluded.prefs
        """, (user_id, json.dumps(cv), json.dumps(prefs)))

        conn.commit()
        conn.close()

    def save_chat(self, user_id, msg, resp):
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO chat (user_id, msg, resp) VALUES (?, ?, ?)",
            (user_id, msg, json.dumps(resp))
        )
        conn.commit()
        conn.close()