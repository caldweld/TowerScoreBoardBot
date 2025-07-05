import os
from fastapi import FastAPI, Request, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests
from urllib.parse import urlencode
from itsdangerous import URLSafeSerializer
import sys
import os

# Add the parent directory to the path so we can import the database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import DatabaseManager

load_dotenv()

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
SESSION_SECRET = os.getenv("SESSION_SECRET")

if not SESSION_SECRET:
    raise ValueError("SESSION_SECRET environment variable is required")

# Initialize database manager
db_manager = DatabaseManager()

app = FastAPI()

# Allow CORS for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://13.239.95.169:5173", "http://13.239.95.169:3000"],  # React dev server and EC2
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
    response = RedirectResponse(url="http://13.239.95.169:3000/dashboard")  # Redirect to your frontend dashboard
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

@app.get("/api/auth/me")
def me(request: Request):
    user_id = get_current_user(request)
    return {"user_id": user_id}

@app.post("/api/auth/logout")
def logout(response: Response):
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie("session")
    return response

# Database API endpoints
@app.get("/api/users")
def get_users(request: Request):
    """Get all users and their tier data (Admin only)"""
    user_id = get_current_user(request)
    if not db_manager.is_bot_admin(user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = db_manager.get_all_users()
    return [
        {
            "discordname": user[0],
            "tiers": {
                f"T{i+1}": user[i+1] for i in range(18)
            }
        }
        for user in users
    ]

@app.get("/api/users/{discord_id}")
def get_user_data(discord_id: str, request: Request):
    """Get tier data for a specific user"""
    user_id = get_current_user(request)
    if not db_manager.is_bot_admin(user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    data = db_manager.get_user_data(discord_id)
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "discord_id": discord_id,
        "tiers": {
            f"T{i+1}": data[i] for i in range(18)
        }
    }

@app.get("/api/leaderboard/wave")
def get_wave_leaderboard(request: Request):
    """Get leaderboard sorted by highest wave per user"""
    user_id = get_current_user(request)
    if not db_manager.is_bot_admin(user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = db_manager.get_all_users()
    leaderboard = []
    
    for user in users:
        username = user[0]
        tiers = user[1:]
        max_wave = 0
        max_wave_tier = None
        
        for i, tier_str in enumerate(tiers):
            if tier_str:
                # Extract wave number from tier string
                import re
                wave_match = re.search(r"Wave:\s*(\d+)", tier_str)
                if wave_match:
                    wave = int(wave_match.group(1))
                    if wave > max_wave:
                        max_wave = wave
                        max_wave_tier = f"T{i+1}"
        
        if max_wave > 0:
            leaderboard.append({
                "username": username,
                "max_wave": max_wave,
                "tier": max_wave_tier
            })
    
    # Sort by max wave descending
    leaderboard.sort(key=lambda x: x["max_wave"], reverse=True)
    return leaderboard

@app.get("/api/leaderboard/coins")
def get_coins_leaderboard(request: Request):
    """Get leaderboard sorted by highest coins per user"""
    user_id = get_current_user(request)
    if not db_manager.is_bot_admin(user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = db_manager.get_all_users()
    leaderboard = []
    
    for user in users:
        username = user[0]
        tiers = user[1:]
        max_coins = 0
        max_coins_tier = None
        
        for i, tier_str in enumerate(tiers):
            if tier_str:
                # Extract coins from tier string
                import re
                coins_match = re.search(r"Coins:\s*([\d.,]+[KMBTQ]?)", tier_str)
                if coins_match:
                    coins_str = coins_match.group(1)
                    # Convert to numeric value
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
                "username": username,
                "max_coins": max_coins,
                "tier": max_coins_tier
            })
    
    # Sort by max coins descending
    leaderboard.sort(key=lambda x: x["max_coins"], reverse=True)
    return leaderboard

@app.get("/api/stats/overview")
def get_stats_overview(request: Request):
    """Get overview statistics"""
    user_id = get_current_user(request)
    if not db_manager.is_bot_admin(user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = db_manager.get_all_users()
    total_users = len(users)
    
    # Count users with data
    users_with_data = sum(1 for user in users if any(user[i+1] for i in range(18)))
    
    return {
        "total_users": total_users,
        "users_with_data": users_with_data,
        "bot_status": "online",
        "database_status": "connected"
    }

@app.get("/api/admin/bot-admins")
def get_bot_admins(request: Request):
    """Get list of bot admins"""
    user_id = get_current_user(request)
    if not db_manager.is_bot_admin(user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    admin_ids = db_manager.get_all_bot_admins()
    return {"admin_ids": admin_ids}

@app.post("/api/admin/add-bot-admin")
def add_bot_admin(discord_id: str, request: Request):
    """Add a user as bot admin"""
    user_id = get_current_user(request)
    if not db_manager.is_bot_admin(user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db_manager.add_bot_admin(discord_id)
    return {"message": f"User {discord_id} added as bot admin"}

@app.delete("/api/admin/remove-bot-admin")
def remove_bot_admin(discord_id: str, request: Request):
    """Remove a user from bot admins"""
    user_id = get_current_user(request)
    if not db_manager.is_bot_admin(user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db_manager.remove_bot_admin(discord_id)
    return {"message": f"User {discord_id} removed from bot admins"}

