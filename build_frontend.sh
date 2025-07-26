#!/bin/bash

echo "🎨 Building frontend..."

# Navigate to frontend directory
cd /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite

echo ""
echo "1. Installing dependencies..."
npm install

echo ""
echo "2. Building frontend..."
npm run build

echo ""
echo "3. Verifying build..."
ls -la dist/

echo ""
echo "✅ Frontend build complete!" 