#!/bin/bash

echo "🔍 Debugging 500 Internal Server Error..."

echo ""
echo "📊 1. Checking nginx status..."
sudo systemctl status nginx

echo ""
echo "📋 2. Testing nginx configuration..."
sudo nginx -t

echo ""
echo "📝 3. Recent nginx error logs..."
sudo tail -20 /var/log/nginx/error.log

echo ""
echo "📝 4. Recent nginx access logs..."
sudo tail -20 /var/log/nginx/access.log

echo ""
echo "🔌 5. Checking if backend is running on port 8000..."
sudo netstat -tlnp | grep :8000

echo ""
echo "🤖 6. Checking backend screen session..."
screen -list | grep backend

echo ""
echo "🌐 7. Testing backend directly..."
curl -I http://localhost:8000/api/auth/me 2>/dev/null || echo "Backend not responding"

echo ""
echo "📁 8. Checking frontend build directory..."
ls -la /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist/

echo ""
echo "🔧 9. Checking file permissions..."
ls -la /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/

echo ""
echo "💡 Troubleshooting tips:"
echo "   - If backend is not running: screen -r backend"
echo "   - If nginx has errors: sudo systemctl reload nginx"
echo "   - If permissions are wrong: sudo chown -R www-data:www-data /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist"
echo "   - To restart everything: ./start_dashboard.sh" 