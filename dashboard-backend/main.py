import os
from fastapi import FastAPI, Request, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests
from urllib.parse import urlencode
from itsdangerous import URLSafeSerializer

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

