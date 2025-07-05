#!/bin/bash

# Kill old screen sessions if they exist
screen -S backend -X quit 2>/dev/null
screen -S frontend -X quit 2>/dev/null
screen -S bot -X quit 2>/dev/null

# Start backend
cd /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-backend
source venv/bin/activate
screen -dmS backend uvicorn main:app --host 0.0.0.0 --port 8000

# Start frontend (Vite dev server)
cd /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite
screen -dmS frontend npm run dev

# Start bot (production static site)
cd /home/ubuntu/discord/bot/TowerScoreBoardBot/
screen -dmS bot python3 main.py

echo "Backend and frontend started in screen sessions 'backend' and 'frontend'."

#chmod +x start_dashboard.sh
