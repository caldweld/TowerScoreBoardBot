#!/bin/bash

echo "🔧 Fixing permission denied error..."

echo ""
echo "1. Checking current ownership..."
ls -la /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/

echo ""
echo "2. Setting correct ownership for nginx..."
sudo chown -R www-data:www-data /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist

echo ""
echo "3. Setting correct permissions..."
sudo chmod -R 755 /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist

echo ""
echo "4. Verifying the fix..."
ls -la /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist/

echo ""
echo "5. Testing if nginx can read the files..."
sudo -u www-data test -r /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist/index.html && echo "✅ nginx can read index.html" || echo "❌ nginx still cannot read index.html"

echo ""
echo "6. Reloading nginx..."
sudo systemctl reload nginx

echo ""
echo "✅ Permission fix complete!"
echo "🌐 Try accessing http://www.toweraus.com now" 