from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import get_connection
from leetcode import fetch_leetcode_stats
import asyncio
import httpx
async def refresh_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, leetcode_name FROM users")
    users = cursor.fetchall()
    conn.close()

    for user in users:
        leetcode_name = user[1]
        if leetcode_name:
            await fetch_leetcode_stats(leetcode_name)
            await asyncio.sleep(0.5)

scheduler=AsyncIOScheduler()
scheduler.add_job(refresh_all_users,"interval", minutes=30)
async def ping_self():
    try:
        async with httpx.AsyncClient() as client:
            await client.get("https://leetmate.onrender.com/count_online")
    except:
        pass

scheduler.add_job(ping_self, "interval", minutes=10)