import os
from fastapi import FastAPI, Request, Depends, HTTPException, Response, Query
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import csv
import io
import json
from datetime import datetime
from dotenv import load_dotenv
import requests
from urllib.parse import urlencode
from itsdangerous import URLSafeSerializer
from sqlalchemy.orm import Session
from dashboard_backend.database import get_db
from dashboard_backend.models import UserData, UserDataHistory, BotAdmin, UserStats
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
            "discordid": user.discordid,
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

@app.get("/api/leaderboard/tier/{tier_num}")
def get_tier_leaderboard(tier_num: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    if not (1 <= tier_num <= 18):
        raise HTTPException(status_code=400, detail="Tier must be between 1 and 18")
    
    users = db.query(UserData).all()
    leaderboard = []
    
    for user in users:
        tier_str = getattr(user, f"T{tier_num}")
        if tier_str and tier_str != "Wave: 0 Coins: 0":
            # Extract wave and coins from tier string
            wave_match = re.search(r"Wave:\s*(\d+)", tier_str)
            coins_match = re.search(r"Coins:\s*([\d.,]+[KMBTQ]?)", tier_str)
            
            wave = int(wave_match.group(1)) if wave_match else 0
            coins = 0
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
                except:
                    coins = 0
            
            if wave > 0 or coins > 0:
                leaderboard.append({
                    "username": user.discordname,
                    "wave": wave,
                    "coins": coins,
                    "coins_formatted": formatNumber(coins) if coins > 0 else "0"
                })
    
    # Sort by wave first, then by coins as tiebreaker
    leaderboard.sort(key=lambda x: (x["wave"], x["coins"]), reverse=True)
    return leaderboard

def formatNumber(num):
    if num >= 1e15:
        return f"{num / 1e15:.1f}Q"
    elif num >= 1e12:
        return f"{num / 1e12:.1f}T"
    elif num >= 1e9:
        return f"{num / 1e9:.1f}B"
    elif num >= 1e6:
        return f"{num / 1e6:.1f}M"
    elif num >= 1e3:
        return f"{num / 1e3:.1f}K"
    else:
        return str(int(num))

@app.get("/api/stats/overview")
def get_stats_overview(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
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

@app.get("/api/export/data")
def export_all_data(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    if not is_bot_admin(user_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all user data
    users = db.query(UserData).all()
    history = db.query(UserDataHistory).all()
    
    # Prepare data for export
    export_data = {
        "export_date": datetime.now().isoformat(),
        "users": [],
        "history": []
    }
    
    # Format user data
    for user in users:
        user_data = {
            "discord_id": user.discordid,
            "discord_name": user.discordname,
            "tiers": {}
        }
        for i in range(18):
            tier_value = getattr(user, f"T{i+1}")
            user_data["tiers"][f"T{i+1}"] = tier_value
        export_data["users"].append(user_data)
    
    # Format history data
    for entry in history:
        history_data = {
            "discord_id": entry.discordid,
            "discord_name": entry.discordname,
            "timestamp": entry.timestamp.isoformat(),
            "tiers": {}
        }
        for i in range(18):
            tier_value = getattr(entry, f"T{i+1}")
            history_data["tiers"][f"T{i+1}"] = tier_value
        export_data["history"].append(history_data)
    
    # Create JSON file in memory
    json_data = json.dumps(export_data, indent=2, default=str)
    json_bytes = json_data.encode('utf-8')
    
    # Create response with file download
    filename = f"tower_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/export/csv")
def export_csv_data(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    if not is_bot_admin(user_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all user data
    users = db.query(UserData).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    header = ["Discord ID", "Discord Name"]
    for i in range(18):
        header.append(f"T{i+1}")
    writer.writerow(header)
    
    # Write data
    for user in users:
        row = [user.discordid, user.discordname]
        for i in range(18):
            tier_value = getattr(user, f"T{i+1}")
            row.append(tier_value or "")
        writer.writerow(row)
    
    # Get CSV content
    csv_content = output.getvalue()
    output.close()
    
    # Create response with file download
    filename = f"tower_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/user/progress")
def get_user_progress(
    request: Request,
    db: Session = Depends(get_db),
    tier: str = Query(..., description="Tier (e.g. t1, t2, etc.)")
):
    user_id = get_current_user(request)
    if not tier.lower().startswith("t") or not tier[1:].isdigit():
        raise HTTPException(status_code=400, detail="Invalid tier format")
    tier_num = int(tier[1:])
    if not (1 <= tier_num <= 18):
        raise HTTPException(status_code=400, detail="Tier must be between t1 and t18")

    history = db.query(UserDataHistory).filter(UserDataHistory.discordid == user_id).order_by(UserDataHistory.timestamp).all()
    progress = []
    for row in history:
        tier_str = getattr(row, f"T{tier_num}")
        if tier_str:
            wave_match = re.search(r"Wave:\s*(\d+)", tier_str)
            wave = int(wave_match.group(1)) if wave_match else 0
            if wave > 0:  # Only include entries with actual wave data
                progress.append({
                    "timestamp": row.timestamp.isoformat(),
                    "wave": wave
                })
    return progress

NUMERIC_STATS_FIELDS = [
    "coins_earned", "cash_earned", "stones_earned", "damage_dealt", "enemies_destroyed", "waves_completed",
    "upgrades_bought", "workshop_upgrades", "workshop_coins_spent", "research_completed", "lab_coins_spent",
    "free_upgrades", "interest_earned", "orb_kills", "death_ray_kills", "thorn_damage", "waves_skipped"
]

def parse_num(val):
    if val is None:
        return 0
    val = str(val).replace(",", "").replace("$", "")
    # Fix common OCR misreads
    val = val.replace("o", "O").replace("l", "1").replace("I", "1")
    mult = 1
    if len(val) > 1 and val[-1] in "KMBTQO":
        unit = val[-1]
        val = val[:-1]
        if unit == "K":
            mult = 1_000
        elif unit == "M":
            mult = 1_000_000
        elif unit == "B":
            mult = 1_000_000_000
        elif unit == "T":
            mult = 1_000_000_000_000
        elif unit == "Q":
            mult = 1_000_000_000_000_000
        elif unit == "O":
            mult = 1_000_000_000_000_000_000
    try:
        return float(val) * mult
    except:
        return 0

@app.get("/api/stats-leaderboard")
def stats_leaderboard(field: str = Query(..., description="Stat field to rank by"), db: Session = Depends(get_db)):
    if field not in NUMERIC_STATS_FIELDS:
        raise HTTPException(status_code=400, detail="Invalid field")
    # For each user, get their highest value for the field
    users = db.query(UserStats.discordid, UserStats.discordname).distinct().all()
    leaderboard = []
    for user in users:
        # Get all entries for this user, get max value for the field
        entries = db.query(UserStats).filter(UserStats.discordid == user.discordid).all()
        max_val = 0
        for entry in entries:
            val = parse_num(getattr(entry, field))
            if val > max_val:
                max_val = val
        leaderboard.append({
            "discordid": user.discordid,
            "username": user.discordname,
            "value": max_val
        })
    leaderboard = [x for x in leaderboard if x["value"] > 0]
    leaderboard.sort(key=lambda x: x["value"], reverse=True)
    return leaderboard

