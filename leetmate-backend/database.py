import sqlite3
from datetime import datetime
from datetime import datetime, timezone, timedelta
IST = timezone(timedelta(hours=5, minutes=30))
def get_ist_now():
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
def get_connection():
    conn=sqlite3.connect("leetmate.db")
    return conn

def init_db():
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("""
           
      CREATE TABLE IF NOT EXISTS 
                   users(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT UNIQUE NOT NULL,
                   password TEXT NOT NULL,
                   branch TEXT NOT NULL,
                   leetcode_name TEXT NOT NULL,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS leetcode_cache(
                   leetcode_name TEXT PRIMARY KEY,
                   total_solved INTEGER,
                   easy INTEGER,
                   medium INTEGER,
                   hard INTEGER,
                   last_updated TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS friendships(
                   username TEXT NOT NULL,
                   friend_username TEXT NOT NULL,
                   PRIMARY KEY(username, friend_username))""")
    try:
      cursor.execute("""ALTER TABLE users ADD COLUMN last_active TIMESTAMP""")
      conn.commit()
    except:
     pass
    conn.commit()
    # conn.execute("DELETE FROM users")
    # conn.commit()
    conn.close()

def create_user(username, password, branch, leetcode_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""INSERT INTO users(username, password, branch, leetcode_name) 
                          VALUES(?,?,?,?)""",
                          (username, password, branch, leetcode_name))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Username already taken")
    conn.close()

def get_user_by_username(username):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?",
                   (username,)
                   )
    user=cursor.fetchone()
    conn.close()
    return user
def leetcode_stats(leetcode_name,total_solved,easy,medium,hard):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("""INSERT INTO leetcode_cache(
                   leetcode_name,total_solved,easy,medium,hard,last_updated)
                   VALUES(?,?,?,?,?,?)
                   ON CONFLICT(leetcode_name) DO UPDATE SET
                   total_solved=excluded.total_solved,
                   easy=excluded.easy,
                   medium=excluded.medium,
                   hard=excluded.hard,
                   last_updated=excluded.last_updated""",
                   (leetcode_name,total_solved,easy,medium,hard,get_ist_now()))
    conn.commit()
    conn.close()