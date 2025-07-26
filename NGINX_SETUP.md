# 🚀 Nginx Setup Guide for Tower Scoreboard

## Overview

This guide sets up nginx to:
- Serve the frontend static files on port 80
- Proxy API calls to the backend running on port 8000
- Handle CORS and security headers
- Provide compression and caching

## Quick Setup

### 1. Run the Setup Script

```bash
# Make the script executable
chmod +x setup_nginx.sh

# Run the setup
./setup_nginx.sh
```

This will:
- Install nginx
- Configure it with our custom settings
- Enable the service
- Test the configuration

### 2. Start Your Services

```bash
# Start backend, build frontend, and start bot
./start_dashboard.sh
```

## Manual Setup (Alternative)

If you prefer to set up nginx manually:

### 1. Install nginx
```bash
sudo apt update
sudo apt install -y nginx
```

### 2. Configure nginx
```bash
# Backup default config
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# Copy our config
sudo cp nginx.conf /etc/nginx/sites-available/toweraus

# Enable our site
sudo ln -sf /etc/nginx/sites-available/toweraus /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Start nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

## Configuration Details

### What the nginx config does:

1. **Frontend Serving** (`location /`):
   - Serves static files from `/home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist`
   - Handles SPA routing with `try_files $uri $uri/ /index.html`
   - Caches static assets for 1 year

2. **API Proxying** (`location /api/`):
   - Proxies all `/api/*` requests to `http://localhost:8000`
   - Preserves headers and handles WebSocket upgrades
   - Handles CORS preflight requests

3. **Security Headers**:
   - X-Frame-Options, XSS Protection, Content-Type-Options
   - Referrer Policy and Content Security Policy

4. **Performance**:
   - Gzip compression for text-based files
   - Long-term caching for static assets

## URL Structure

After setup, your URLs will be:

- **Frontend**: `http://www.toweraus.com`
- **API Endpoints**: `http://www.toweraus.com/api/*`
  - Examples:
    - `http://www.toweraus.com/api/auth/login`
    - `http://www.toweraus.com/api/leaderboard/wave`
    - `http://www.toweraus.com/api/stats/overview`

## Troubleshooting

### Check nginx status
```bash
sudo systemctl status nginx
```

### View nginx logs
```bash
# Error logs
sudo tail -f /var/log/nginx/error.log

# Access logs
sudo tail -f /var/log/nginx/access.log
```

### Test nginx configuration
```bash
sudo nginx -t
```

### Reload nginx after config changes
```bash
sudo systemctl reload nginx
```

### Common Issues

1. **Port 80 already in use**:
   ```bash
   # Check what's using port 80
   sudo netstat -tlnp | grep :80
   
   # Stop conflicting service (e.g., Apache)
   sudo systemctl stop apache2
   ```

2. **Permission denied**:
   ```bash
   # Ensure nginx can read the frontend directory
   sudo chown -R www-data:www-data /home/ubuntu/discord/bot/TowerScoreBoardBot/dashboard-frontend-vite/dist
   ```

3. **Backend not responding**:
   ```bash
   # Check if backend is running
   screen -r backend
   
   # Or check port 8000
   sudo netstat -tlnp | grep :8000
   ```

## Security Considerations

1. **Firewall**: Ensure port 80 is open in your firewall
2. **SSL**: Consider adding HTTPS with Let's Encrypt
3. **Rate Limiting**: Add rate limiting for API endpoints if needed
4. **Logs**: Monitor nginx logs for suspicious activity

## Performance Tips

1. **Caching**: Static assets are cached for 1 year
2. **Compression**: Gzip is enabled for text files
3. **CDN**: Consider using a CDN for global performance
4. **Monitoring**: Use tools like `htop` to monitor server resources

## Next Steps

After nginx is set up:

1. Test the frontend at `http://www.toweraus.com`
2. Verify API calls work (try logging in)
3. Monitor logs for any issues
4. Consider setting up SSL/HTTPS
5. Set up monitoring and alerts 