#!/bin/bash

echo "🎨 Building frontend with proper permissions..."

# Navigate to frontend directory
cd /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite

echo ""
echo "1. Temporarily changing ownership for build..."
sudo chown -R ubuntu:ubuntu dist/

echo ""
echo "2. Installing dependencies..."
npm install

echo ""
echo "3. Building frontend..."
npm run build

echo ""
echo "4. Setting correct ownership for nginx..."
sudo chown -R www-data:www-data dist/

echo ""
echo "5. Setting correct permissions..."
sudo chmod -R 755 dist/

echo ""
echo "6. Verifying build..."
ls -la dist/

echo ""
echo "✅ Frontend build complete!"
echo "🌐 nginx can now serve the updated frontend" 