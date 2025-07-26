#!/bin/bash

echo "🔧 Fixing nginx issues..."

echo ""
echo "1. Checking if dist directory exists..."
if [ ! -d "/home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist" ]; then
    echo "❌ dist directory not found. Building frontend first..."
    chmod +x build_frontend.sh
    ./build_frontend.sh
else
    echo "✅ dist directory exists"
fi

echo ""
echo "2. Fixing permissions for entire frontend directory..."
sudo chown -R www-data:www-data /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist
sudo chmod -R 755 /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist

echo ""
echo "3. Checking if index.html exists..."
if [ -f "/home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist/index.html" ]; then
    echo "✅ index.html exists"
    ls -la /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist/index.html
else
    echo "❌ index.html not found. Building frontend..."
    chmod +x build_frontend.sh
    ./build_frontend.sh
fi

echo ""
echo "4. Creating a simpler nginx config to avoid redirection cycle..."
cat > nginx_fixed.conf << 'EOF'
server {
    listen 80;
    server_name www.toweraus.com toweraus.com;

    # Frontend static files
    location / {
        root /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API calls to backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Basic gzip compression
    gzip on;
    gzip_types text/plain text/css text/javascript application/javascript;
}
EOF

echo ""
echo "5. Installing the fixed nginx config..."
sudo cp nginx_fixed.conf /etc/nginx/sites-available/toweraus

echo ""
echo "6. Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ nginx configuration is valid"
    echo "Reloading nginx..."
    sudo systemctl reload nginx
else
    echo "❌ nginx configuration has errors"
    exit 1
fi

echo ""
echo "7. Testing the setup..."
echo "Testing frontend access..."
curl -I http://localhost/ 2>/dev/null | head -1

echo ""
echo "✅ Fix complete!"
echo "🌐 Try accessing http://www.toweraus.com now" 