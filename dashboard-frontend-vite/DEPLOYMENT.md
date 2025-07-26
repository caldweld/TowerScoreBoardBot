# Frontend Deployment Guide

## Deploying to Porkbun Static Hosting

### Prerequisites
- Porkbun account with static hosting plan
- Domain name (optional but recommended)
- SSL certificate (included with Porkbun hosting)

### Step 1: Build the Frontend

1. Navigate to the frontend directory:
   ```bash
   cd dashboard-frontend-vite
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build for production:
   ```bash
   npm run build
   ```

   This creates a `dist` folder with optimized static files.

### Step 2: Configure Environment Variables

1. Create a `.env` file in the frontend directory:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` to set your API URL:
   ```
   # For production (your AWS server)
   VITE_API_URL=http://13.239.95.169:8000
   
   # Or if you want to use HTTPS for API calls
   # VITE_API_URL=https://your-domain.com:8000
   ```

3. Rebuild after changing environment variables:
   ```bash
   npm run build
   ```

### Step 3: Upload to Porkbun

1. Log into your Porkbun account
2. Go to your domain's hosting control panel
3. Navigate to the file manager or FTP section
4. Upload all contents of the `dist` folder to your web root directory

### Step 4: Configure Backend CORS

Your FastAPI backend needs to accept requests from your Porkbun domain. Update your backend CORS configuration in `dashboard_backend/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://your-domain.com",  # Your Porkbun domain
        "https://www.your-domain.com",  # With www
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 5: Test Your Deployment

1. Visit your domain to ensure the frontend loads
2. Test the login functionality
3. Verify that API calls work correctly

## Performance Optimization

### Expected Performance:
- **Static files**: ~50-100ms globally (served from Porkbun's CDN)
- **API calls**: ~100-300ms (depending on geographic distance to your AWS server)
- **Database queries**: ~1-10ms (excellent, same server as backend)

### Tips for Better Performance:
1. **Use a CDN**: Porkbun includes CDN for static files
2. **Optimize images**: Use WebP format and appropriate sizes
3. **Enable compression**: Porkbun handles this automatically
4. **Consider API caching**: Implement caching for frequently accessed data

## Troubleshooting

### Common Issues:

1. **CORS Errors**: Ensure your backend CORS configuration includes your Porkbun domain
2. **API Connection Issues**: Verify your API URL is correct and accessible
3. **SSL Warnings**: Porkbun provides SSL certificates automatically
4. **Build Errors**: Check that all dependencies are installed and environment variables are set

### SSL Configuration:
- Porkbun provides free SSL certificates
- Your site will be served over HTTPS automatically
- API calls to your backend will still use HTTP unless you configure HTTPS on your backend

## Alternative Deployment Options

### Option 1: Keep Current Setup
- Frontend: Deploy to Porkbun (static hosting + SSL)
- Backend: Keep on your current AWS server
- Database: Keep on your current AWS server

### Option 2: Full Cloud Migration
- Frontend: Porkbun (static hosting)
- Backend: Deploy to a cloud service (Railway, Render, Heroku, etc.)
- Database: Use a managed PostgreSQL service (Railway, Supabase, etc.)

## Security Considerations

1. **Environment Variables**: Never commit `.env` files to version control
2. **API Security**: Ensure your backend has proper authentication
3. **HTTPS**: Porkbun provides SSL certificates automatically
4. **CORS**: Configure CORS properly to prevent unauthorized access 