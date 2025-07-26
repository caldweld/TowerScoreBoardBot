#!/bin/bash

echo "🚀 Deploying nginx configuration for Tower Scoreboard..."

# Check if we're in the right directory
if [ ! -f "nginx.conf" ]; then
    echo "❌ Error: nginx.conf not found in current directory"
    echo "Please run this script from the TowerScoreBoardBot directory"
    exit 1
fi

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

# Ensure frontend directory exists and has correct permissions
echo "🔧 Setting up frontend directory permissions..."
sudo mkdir -p /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist
sudo chown -R www-data:www-data /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ nginx configuration is valid!"
    
    # Start nginx
    echo "🚀 Starting nginx..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
    
    echo "✅ nginx deployment complete!"
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
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Run ./start_dashboard.sh to start your services"
    echo "   2. Test the frontend at http://www.toweraus.com"
    echo "   3. Verify API calls work (try logging in)"
else
    echo "❌ nginx configuration test failed!"
    echo "Please check the configuration and try again."
    exit 1
fi 