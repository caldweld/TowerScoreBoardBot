#!/bin/bash

# Kill old screen sessions if they exist
screen -S backend -X quit 2>/dev/null
screen -S frontend -X quit 2>/dev/null

# Start backend
cd /dashboard-backend
source venv/bin/activate
screen -dmS backend uvicorn main:app --host 0.0.0.0 --port 8000

# Start frontend (production static site)
cd /dashboard-frontend
screen -dmS frontend npx serve -s build -l 3000

echo "Backend and frontend started in screen sessions 'backend' and 'frontend'."
