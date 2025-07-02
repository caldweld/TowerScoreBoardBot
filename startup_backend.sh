cd discord/bot/TowerScoreBoardBot/dashboard-backend/

source venv/bin/activate
screen -dmS backend uvicorn main:app --host 0.0.0.0 --port 8000