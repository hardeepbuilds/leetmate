from fastapi import FastAPI,HTTPException, Depends, Query
from pydantic import BaseModel, Field
from enum import Enum
from database import get_connection, get_ist_now, init_db, create_user, get_user_by_username
import bcrypt
from auth import create_access_token, get_current_user
from leetcode import fetch_leetcode_stats
from scheduler import scheduler
from fastapi.middleware.cors import CORSMiddleware
import os

init_db()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#signup______________________________________________________________________________________________________________________________________
class Branch(str, Enum):
    CSE="CSE"
    IT="IT"
    ECE="ECE"
class CreateUser(BaseModel):
    username:str
    password:str
    branch:Branch
    leetcode_name:str
@app.post("/signup")
async def signup(data: CreateUser):
    stats=await fetch_leetcode_stats(data.leetcode_name)
    if stats is None:
        raise HTTPException(status_code=400, detail="LeetCode username not found")
    hashed_password = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt())
    try:
        create_user(
            data.username,
            hashed_password.decode(),
            data.branch.value,
            data.leetcode_name
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "User created successfully"}
#login_______________________________________________________________________________________________________________________________________
class LoginUser(BaseModel):
    username:str
    password:str
@app.post("/login")
def login(data:LoginUser):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("""SELECT * FROM users WHERE username=%s""",(data.username,))
    user=cursor.fetchone()
    conn.close()
    if user is None:
        raise HTTPException(status_code=401, detail="invalid username or password")
    stored_hash=user[2].encode()
    if not bcrypt.checkpw(data.password.encode(),stored_hash):
        raise HTTPException(status_code=401, detail="invalid username or password")
    token=create_access_token(data.username)
    return{"access_token": token,"token_type":"Bearer"}
from leetcode import fetch_leetcode_stats
#me/profile__________________________________________________________________________________________________________________________________
@app.get("/me")
async def user_profile(current_user: str = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT username, branch, leetcode_name 
                      FROM users WHERE username=%s""", (current_user,))
    user_row = cursor.fetchone()

    if user_row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    leetcode_name = user_row[2]

    cursor.execute("""SELECT total_solved, easy, medium, hard, last_updated, submission_calendar
                      FROM leetcode_cache WHERE leetcode_name=%s""", (leetcode_name,))
    cached = cursor.fetchone()

    cursor.execute("""SELECT leetcode_name, total_solved 
                      FROM leetcode_cache 
                      ORDER BY total_solved DESC LIMIT 1""")
    top_student = cursor.fetchone()

    conn.close()

    if cached is None:
        stats = await fetch_leetcode_stats(leetcode_name)
        if stats is None:
            raise HTTPException(status_code=404, detail="LeetCode user not found")
        total = stats["total_solved"]
        easy = stats["easy"]
        medium = stats["medium"]
        hard = stats["hard"]
        last_updated = "just now"
    else:
        total = cached[0]
        easy = cached[1]
        medium = cached[2]
        hard = cached[3]
        last_updated = cached[4]

    gap = (top_student[1] - total) if top_student else 0
    if gap<0:
        gap=0
        top_name="You"
    top_name = top_student[0] if top_student else "nobody yet"

    return {
        "username": user_row[0],
        "branch": user_row[1],
        "leetcode_name": leetcode_name,
        "total_solved": total,
        "easy": easy,
        "medium": medium,
        "hard": hard,
        "last_updated": last_updated,
        "gap_from_top": gap,
        "top_student": top_name,
        "submission_calendar":cached[5] if cached else "{}"
    }
#leaderboard___________________________________________________________________________________________________________________________
@app.get("/leaderboard")
def leaderboard(current_user:str=Depends(get_current_user)):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("""SELECT lc.leetcode_name,u.username, u.branch, lc.total_solved, lc.easy, lc.medium, lc.hard
                   FROM leetcode_cache lc
                   JOIN users u ON lc.leetcode_name=u.leetcode_name
                   ORDER BY lc.total_solved DESC""")
    rows=cursor.fetchall()
    conn.close()
    return [
    {
        "rank":index+1,
        "username":row[1],
        "leetcode_name":row[0],
        "branch":row[2],
        "total_solved":row[3],
        "easy":row[4],
        "medium":row[5],
        "hard":row[6]
    }
    for index, row in enumerate(rows)
    ]
#add-friend__________________________________________________________________________________________________________________________________________
class AddFriend(BaseModel):
    friend_username:str
@app.post("/add-friend")
def add_friend(data:AddFriend, current_user:str=Depends(get_current_user)):
    if data.friend_username==current_user:
        raise HTTPException(status_code=400, detail="you can't add yourself as a friend")
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("""SELECT username 
                   FROM users
                   WHERE username=%s""",
                   (data.friend_username,))
    row=cursor.fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="user not found")
    try:
        cursor.execute("""INSERT INTO friendships (username,friend_username)
                       VALUES(%s,%s)""",
                       (current_user,data.friend_username,))
        conn.commit()
    except Exception:
        conn.close()
        raise HTTPException(status_code=400,detail="already friends")
    conn.close()
    return{"message":f"{data.friend_username} added as friend"}
#friends__________________________________________________________________________________________________________________________________________
@app.get("/friends")
def friends(current_user:str=Depends(get_current_user)):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("""SELECT lc.total_solved
                   FROM users u
                   JOIN leetcode_cache lc ON u.leetcode_name=lc.leetcode_name
                   WHERE u.username=%s""",(current_user,))
    me=cursor.fetchone()
    my_total=me[0]if me else 0
    cursor.execute("""SELECT f.friend_username, u.branch, lc.total_solved, lc.easy, lc.medium, lc.hard, lc.submission_calendar
                   FROM friendships f
                   JOIN users u ON f.friend_username=u.username
                   JOIN leetcode_cache lc ON u.leetcode_name=lc.leetcode_name
                   WHERE f.username=%s""",
                   (current_user,))
    rows=cursor.fetchall()
    conn.close()
    return[{
        "friend_name":row[0],
        "branch":row[1],
        "total_solved":row[2],
        "easy":row[3],
        "medium":row[4],
        "hard":row[5],
        "gap":row[2]-my_total,
        "submission_calendar":row[6] or "{}"
      }for row in rows
    ]
    
#online-count__________________________________________________________________________________________________________________________________________
@app.get("/count_online")
def count_online():
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("""SELECT COUNT(*) FROM users 
               WHERE last_active IS NOT NULL 
               AND last_active::timestamp >= NOW() - INTERVAL '5 minutes'""")
    count=cursor.fetchone()[0]
    conn.close()
    return {"online_count": count}
@app.on_event("startup")
async def start_scheduler():
    scheduler.start()
@app.on_event("shutdown")
async def stop_scheduler():
    scheduler.shutdown() 
#feeback__________________________________________________________________________________________________________________________________________
class FeedbackRequest(BaseModel):
    message: str

@app.post("/feedback")
def submit_feedback(data: FeedbackRequest, current_user: str = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO feedback (username, message, submitted_at)
        VALUES (%s,%s,%s)
    """, (current_user, data.message, get_ist_now()))
    conn.commit()
    conn.close()
    return {"message": "Feedback received — thank you!"}

@app.get("/feedback/all")
def get_all_feedback(admin_key: str = Query(...)):
    if admin_key != os.getenv("ADMIN_KEY"):
        raise HTTPException(status_code=403, detail="Not authorized")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, message, submitted_at FROM feedback ORDER BY submitted_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"username": r[0], "message": r[1], "submitted_at": r[2]} for r in rows]