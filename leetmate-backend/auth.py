from fastapi import Header,HTTPException, Depends
from dotenv import load_dotenv
from datetime import datetime,timedelta
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_connection
import os
from datetime import datetime, timezone, timedelta
IST = timezone(timedelta(hours=5, minutes=30))
def get_ist_now():
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
bearer_scheme = HTTPBearer()
load_dotenv()
SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")
def create_access_token(username:str):
    expire_time=datetime.utcnow()+timedelta(minutes=30)
    payload = {
        "sub":username,
        "exp":expire_time
    }
    token=jwt.encode(payload, SECRET_KEY,algorithm=ALGORITHM)
    return token
def decode_access_token(token:str):
    try:
        payload=jwt.decode(token,SECRET_KEY, algorithms=[ALGORITHM])
        username=payload.get("sub")
        return username
    except JWTError:
        return None
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    username = decode_access_token(token)
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("""UPDATE users SET last_active=%s WHERE username=%s""",
                   (datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), username,))
    conn.commit()
    conn.close()
    return username