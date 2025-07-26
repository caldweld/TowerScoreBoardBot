#!/bin/bash

echo "🔧 Fixing 500 Internal Server Error..."

echo ""
echo "1. Checking if backend is running..."
if ! sudo netstat -tlnp | grep :8000 > /dev/null; then
    echo "❌ Backend not running on port 8000"
    echo "Starting backend..."
    cd /home/ubuntu/discord/bot/TowerScoreBoardBot
    source venv/bin/activate
    screen -dmS backend uvicorn dashboard_backend.main:app --host 0.0.0.0 --port 8000
    sleep 3
else
    echo "✅ Backend is running on port 8000"
fi

echo ""
echo "2. Testing backend directly..."
if curl -s http://localhost:8000/api/auth/me > /dev/null; then
    echo "✅ Backend is responding"
else
    echo "❌ Backend is not responding properly"
    echo "Checking backend logs..."
    screen -r backend
    exit 1
fi

echo ""
echo "3. Checking frontend build..."
if [ ! -d "/home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist" ]; then
    echo "❌ Frontend not built"
    echo "Building frontend..."
    cd /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite
    npm install
    npm run build
else
    echo "✅ Frontend build exists"
fi

echo ""
echo "4. Fixing permissions..."
sudo chown -R www-data:www-data /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist

echo ""
echo "5. Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ nginx configuration is valid"
    echo "Reloading nginx..."
    sudo systemctl reload nginx
else
    echo "❌ nginx configuration has errors"
    echo "Using simplified configuration..."
    sudo cp nginx_simple.conf /etc/nginx/sites-available/toweraus
    sudo nginx -t && sudo systemctl reload nginx
fi

echo ""
echo "6. Testing the full setup..."
echo "Testing frontend..."
curl -I http://localhost/ 2>/dev/null | head -1

echo "Testing API proxy..."
curl -I http://localhost/api/auth/me 2>/dev/null | head -1

echo ""
echo "✅ Fix complete! Try accessing http://www.toweraus.com now"
echo ""
echo "If still getting 500 errors, run: ./debug_nginx.sh" 