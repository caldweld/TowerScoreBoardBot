#!/bin/bash

echo "Building Tower Scoreboard Frontend..."

# Navigate to frontend directory
cd dashboard-frontend-vite

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build for production
echo "Building for production..."
npm run build

echo "Build complete! Files are in dashboard-frontend-vite/dist/"
echo ""
echo "Next steps:"
echo "1. Upload contents of dist/ folder to your Porkbun hosting"
echo "2. Update backend CORS configuration to include your domain"
echo "3. Test the deployment" 