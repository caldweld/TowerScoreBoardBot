#!/bin/bash

echo "🔧 Setting up nginx for Tower Scoreboard..."

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install nginx
echo "📦 Installing nginx..."
sudo apt install -y nginx

# Stop nginx to configure it
echo "⏹️ Stopping nginx..."
sudo systemctl stop nginx

# Backup default nginx config
echo "💾 Backing up default nginx config..."
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# Copy our custom config
echo "📝 Installing custom nginx config..."
sudo cp nginx.conf /etc/nginx/sites-available/toweraus

# Enable our site and disable default
echo "🔗 Enabling Tower Scoreboard site..."
sudo ln -sf /etc/nginx/sites-available/toweraus /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ nginx configuration is valid!"
    
    # Start nginx
    echo "🚀 Starting nginx..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
    
    echo "✅ nginx setup complete!"
    echo ""
    echo "📋 Configuration summary:"
    echo "   - Frontend: http://www.toweraus.com"
    echo "   - API calls: http://www.toweraus.com/api/* (proxied to backend:8000)"
    echo "   - Static files: served from /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist"
    echo ""
    echo "💡 Useful commands:"
    echo "   - View nginx status: sudo systemctl status nginx"
    echo "   - View nginx logs: sudo tail -f /var/log/nginx/error.log"
    echo "   - Reload nginx: sudo systemctl reload nginx"
else
    echo "❌ nginx configuration test failed!"
    echo "Please check the configuration and try again."
    exit 1
fi 