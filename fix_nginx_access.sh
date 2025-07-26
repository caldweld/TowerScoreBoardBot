#!/bin/bash

echo "🔧 Fixing nginx directory access..."

echo ""
echo "1. Adding www-data to ubuntu group..."
sudo gpasswd -a www-data ubuntu

echo ""
echo "2. Setting directory permissions for the entire path..."
sudo chmod g+x /home/ubuntu
sudo chmod g+x /home/ubuntu/discord
sudo chmod g+x /home/ubuntu/discord/bot
sudo chmod g+x /home/ubuntu/discord/bot/TowerScoreBoardBot
sudo chmod g+x /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite
sudo chmod g+x /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist

echo ""
echo "3. Testing nginx access..."
sudo -u www-data stat /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist/index.html

if [ $? -eq 0 ]; then
    echo "✅ nginx can now access the files!"
else
    echo "❌ nginx still cannot access the files"
    exit 1
fi

echo ""
echo "4. Reloading nginx..."
sudo systemctl reload nginx

echo ""
echo "✅ nginx access fixed!"
echo "🌐 Try accessing http://www.toweraus.com now" 