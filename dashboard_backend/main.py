import os
from fastapi import FastAPI, Request, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests
from urllib.parse import urlencode
from itsdangerous import URLSafeSerializer
from sqlalchemy.orm import Session
from database import get_db
from models import UserData, UserDataHistory, BotAdmin
import re

load_dotenv()

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
SESSION_SECRET = os.getenv("SESSION_SECRET")

if not SESSION_SECRET:
    raise ValueError("SESSION_SECRET environment variable is required")

app = FastAPI()

# Allow CORS for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://13.239.95.169:5173", "http://13.239.95.169:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DISCORD_AUTH_BASE = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_API_BASE = "https://discord.com/api"

serializer = URLSafeSerializer(SESSION_SECRET, salt="discord-login")

def create_session(user_id: str) -> str:
    return serializer.dumps({"user_id": user_id})

@app.get("/api/auth/login")
def login():
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify",
        "prompt": "consent"
    }
    url = f"{DISCORD_AUTH_BASE}?{urlencode(params)}"
    return RedirectResponse(url)

@app.get("/api/auth/callback")
def callback(code: str, response: Response):
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "scope": "identify"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(DISCORD_TOKEN_URL, data=data, headers=headers)
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get token from Discord")
    tokens = r.json()
    access_token = tokens["access_token"]

    # Get user info
    user_resp = requests.get(
        f"{DISCORD_API_BASE}/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    user = user_resp.json()
    user_id = user["id"]

    # Set session cookie
    session_token = create_session(user_id)
    response = RedirectResponse(url="http://13.239.95.169:3000/dashboard")
    response.set_cookie("session", session_token, httponly=True, samesite="lax")
    return response

def get_current_user(request: Request):
    session_token = request.cookies.get("session")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        data = serializer.loads(session_token)
        return data["user_id"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")

def is_bot_admin(user_id: str, db: Session):
    return db.query(BotAdmin).filter(BotAdmin.discordid == user_id).first() is not None

@app.get("/api/auth/me")
def me(request: Request):
    user_id = get_current_user(request)
    return {"user_id": user_id}

@app.post("/api/auth/logout")
def logout(response: Response):
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie("session")
    return response

@app.get("/api/users")
def get_users(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    if not is_bot_admin(user_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    users = db.query(UserData).all()
    return [
        {
            "discordname": user.discordname,
            "tiers": {f"T{i+1}": getattr(user, f"T{i+1}") for i in range(18)}
        }
        for user in users
    ]

@app.get("/api/users/{discord_id}")
def get_user_data(discord_id: str, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    if not is_bot_admin(user_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    user = db.query(UserData).filter(UserData.discordid == discord_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "discord_id": user.discordid,
        "tiers": {f"T{i+1}": getattr(user, f"T{i+1}") for i in range(18)}
    }

@app.get("/api/leaderboard/wave")
def get_wave_leaderboard(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    if not is_bot_admin(user_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    users = db.query(UserData).all()
    leaderboard = []
    for user in users:
        max_wave = 0
        max_wave_tier = None
        for i in range(18):
            tier_str = getattr(user, f"T{i+1}")
            if tier_str:
                wave_match = re.search(r"Wave:\s*(\d+)", tier_str)
                if wave_match:
                    wave = int(wave_match.group(1))
                    if wave > max_wave:
                        max_wave = wave
                        max_wave_tier = f"T{i+1}"
        if max_wave > 0:
            leaderboard.append({
                "username": user.discordname,
                "max_wave": max_wave,
                "tier": max_wave_tier
            })
    leaderboard.sort(key=lambda x: x["max_wave"], reverse=True)
    return leaderboard

@app.get("/api/leaderboard/coins")
def get_coins_leaderboard(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    if not is_bot_admin(user_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    users = db.query(UserData).all()
    leaderboard = []
    for user in users:
        max_coins = 0
        max_coins_tier = None
        for i in range(18):
            tier_str = getattr(user, f"T{i+1}")
            if tier_str:
                coins_match = re.search(r"Coins:\s*([\d.,]+[KMBTQ]?)", tier_str)
                if coins_match:
                    coins_str = coins_match.group(1)
                    multiplier = 1
                    if coins_str.endswith("K"):
                        multiplier = 1_000
                        coins_str = coins_str[:-1]
                    elif coins_str.endswith("M"):
                        multiplier = 1_000_000
                        coins_str = coins_str[:-1]
                    elif coins_str.endswith("B"):
                        multiplier = 1_000_000_000
                        coins_str = coins_str[:-1]
                    elif coins_str.endswith("T"):
                        multiplier = 1_000_000_000_000
                        coins_str = coins_str[:-1]
                    elif coins_str.endswith("Q"):
                        multiplier = 1_000_000_000_000_000
                        coins_str = coins_str[:-1]
                    try:
                        coins = float(coins_str.replace(",", "")) * multiplier
                        if coins > max_coins:
                            max_coins = coins
                            max_coins_tier = f"T{i+1}"
                    except:
                        pass
        if max_coins > 0:
            leaderboard.append({
                "username": user.discordname,
                "max_coins": max_coins,
                "tier": max_coins_tier
            })
    leaderboard.sort(key=lambda x: x["max_coins"], reverse=True)
    return leaderboard

@app.get("/api/stats/overview")
def get_stats_overview(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    if not is_bot_admin(user_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    users = db.query(UserData).all()
    total_users = len(users)
    users_with_data = sum(1 for user in users if any(getattr(user, f"T{i+1}") for i in range(18)))
    return {
        "total_users": total_users,
        "users_with_data": users_with_data,
        "bot_status": "online",
        "database_status": "connected"
    }

@app.get("/api/admin/bot-admins")
def get_bot_admins(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    if not is_bot_admin(user_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    admin_ids = [admin.discordid for admin in db.query(BotAdmin).all()]
    return {"admin_ids": admin_ids}

@app.post("/api/admin/add-bot-admin")
def add_bot_admin(discord_id: str, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    if not is_bot_admin(user_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    db.add(BotAdmin(discordid=discord_id))
    db.commit()
    return {"message": f"User {discord_id} added as bot admin"}

@app.delete("/api/admin/remove-bot-admin")
def remove_bot_admin(discord_id: str, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    if not is_bot_admin(user_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    db.query(BotAdmin).filter(BotAdmin.discordid == discord_id).delete()
    db.commit()
    return {"message": f"User {discord_id} removed from bot admins"}

