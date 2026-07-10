from datetime import datetime
from datetime import datetime, timezone, timedelta
import psycopg2
import os
from dotenv import load_dotenv
IST = timezone(timedelta(hours=5, minutes=30))
def get_ist_now():
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
load_dotenv()
def get_connection():
    conn = psycopg2.connect(
        host="aws-0-ap-northeast-1.pooler.supabase.com",
        database="postgres",
        user="postgres.uvidacalykworeodxkcb",
        password=os.getenv("DB_PASSWORD"),
        port=5432,
        sslmode="require"
    )
    return conn

def init_db():
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("""
           
      CREATE TABLE IF NOT EXISTS 
                   users(
                   id SERIAL PRIMARY KEY,
                   username TEXT UNIQUE NOT NULL,
                   password TEXT NOT NULL,
                   branch TEXT NOT NULL,
                   leetcode_name TEXT UNIQUE NOT NULL,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   last_active TIMESTAMP
                   )
                   """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS leetcode_cache(
                   leetcode_name TEXT UNIQUE PRIMARY KEY,
                   total_solved INTEGER,
                   easy INTEGER,
                   medium INTEGER,
                   hard INTEGER,
                   last_updated TEXT)""")
    cursor.execute("""
     CREATE TABLE IF NOT EXISTS friendships (
            username TEXT NOT NULL,
            friend_username TEXT NOT NULL,
            PRIMARY KEY (username, friend_username)
    )
""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            submitted_at TEXT)""")
    conn.commit()
    # conn.execute("DELETE FROM users")
    # conn.commit()
    conn.close()

def create_user(username, password, branch, leetcode_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""INSERT INTO users(username, password, branch, leetcode_name) 
                          VALUES(%s,%s,%s,%s)""",
                          (username, password, branch, leetcode_name))
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.close()
        raise ValueError("Username already taken")
    conn.close()

def get_user_by_username(username):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=%s",
                   (username,)
                   )
    user=cursor.fetchone()
    conn.close()
    return user
def leetcode_stats(leetcode_name, total_solved, easy, medium, hard):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO leetcode_cache(leetcode_name, total_solved, easy, medium, hard, last_updated)
        VALUES(%s,%s,%s,%s,%s,%s)
        ON CONFLICT(leetcode_name) DO UPDATE SET
            total_solved=EXCLUDED.total_solved,
            easy=EXCLUDED.easy,
            medium=EXCLUDED.medium,
            hard=EXCLUDED.hard,
            last_updated=EXCLUDED.last_updated
    """, (leetcode_name, total_solved, easy, medium, hard, get_ist_now()))
    conn.commit()
    conn.close()