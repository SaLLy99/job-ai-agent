import sqlite3

DB_PATH = "agent.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS profile (
        user_id TEXT PRIMARY KEY,
        cv TEXT,
        prefs TEXT,
        identity TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS chat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        msg TEXT,
        resp TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS crawler_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crawler_name TEXT,
        total INTEGER,
        validated INTEGER,
        rejected INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    try:
        c.execute("SELECT identity FROM profile LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE profile ADD COLUMN identity TEXT")

    conn.commit()
    conn.close()
