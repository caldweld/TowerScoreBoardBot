#!/bin/bash

# Kill old screen sessions if they exist
screen -S backend -X quit 2>/dev/null
screen -S frontend -X quit 2>/dev/null
screen -S bot -X quit 2>/dev/null

# Start backend
cd /home/ubuntu/discord/bot/TowerScoreBoardBot
source venv/bin/activate
screen -dmS backend uvicorn dashboard_backend.main:app --host 0.0.0.0 --port 8000

# Start frontend (Vite dev server)
cd /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite
screen -dmS frontend npm run dev

# Start bot
cd /home/ubuntu/discord/bot/TowerScoreBoardBot/
screen -dmS bot python3 bot.py

echo "Backend, frontend, and bot started in screen sessions 'backend', 'frontend', and 'bot'."

#chmod +x start_dashboard.sh
