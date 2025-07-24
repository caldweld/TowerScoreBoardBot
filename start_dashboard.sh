#!/bin/bash

echo "🚀 Starting Tower Scoreboard System..."

# Initialize database schema
echo "🔧 Initializing database schema..."
cd /home/ubuntu/discord/bot/TowerScoreBoardBot
source venv/bin/activate
python3 dashboard_backend/init_db.py

# Kill old screen sessions if they exist
screen -S backend -X quit 2>/dev/null
screen -S frontend -X quit 2>/dev/null
screen -S bot -X quit 2>/dev/null

# Start backend
echo "📊 Starting backend server..."
cd /home/ubuntu/discord/bot/TowerScoreBoardBot
source venv/bin/activate
screen -dmS backend uvicorn dashboard_backend.main:app --host 0.0.0.0 --port 8000

# Start frontend (Vite dev server)
echo "🎨 Starting frontend server..."
cd /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite
screen -dmS frontend npm run dev

# Start bot with Gemini AI integration
echo "🤖 Starting Discord bot with Gemini AI..."
cd /home/ubuntu/discord/bot/TowerScoreBoardBot/
screen -dmS bot python3 bot.py

echo "✅ All services started successfully!"
echo "📊 Backend: screen session 'backend'"
echo "🎨 Frontend: screen session 'frontend'" 
echo "🤖 Discord Bot: screen session 'bot'"
echo ""
echo "💡 Use 'screen -r backend' to view backend logs"
echo "💡 Use 'screen -r frontend' to view frontend logs"
echo "💡 Use 'screen -r bot' to view bot logs"

