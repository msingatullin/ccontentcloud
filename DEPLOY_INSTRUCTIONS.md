# 🚀 Frontend Deployment Instructions

## Quick Deploy Options

### Option 1: Vercel Dashboard (Recommended)
1. Go to [vercel.com](https://vercel.com)
2. Sign up/Login with GitHub
3. Click "New Project"
4. Upload the `frontend-deploy-*.tar.gz` file
5. Extract and select the `build` folder
6. Set framework to "Create React App"
7. Add environment variables (see below)
8. Deploy!

### Option 2: Netlify
1. Go to [netlify.com](https://netlify.com)
2. Drag & drop the `build` folder
3. Add environment variables
4. Deploy!

### Option 3: GitHub Pages
1. Push to GitHub repository
2. Enable GitHub Pages in settings
3. Set source to `build` folder
4. Deploy!

## Environment Variables
Add these in your deployment platform:

```
REACT_APP_API_URL=https://goinvesting.ai
REACT_APP_API_BASE_URL=https://goinvesting.ai/api/v1
REACT_APP_WS_URL=wss://goinvesting.ai/ws
REACT_APP_JWT_STORAGE_KEY=ai_content_orchestrator_token
REACT_APP_REFRESH_TOKEN_KEY=ai_content_orchestrator_refresh_token
REACT_APP_APP_NAME=AI Content Orchestrator
REACT_APP_APP_VERSION=1.0.0
REACT_APP_ENVIRONMENT=production
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_ERROR_REPORTING=true
REACT_APP_ENABLE_PWA=true
REACT_APP_BILLING_ENABLED=true
REACT_APP_YOOKASSA_SHOP_ID=1134145
REACT_APP_ENABLE_SERVICE_WORKER=true
REACT_APP_CACHE_VERSION=1.0.0
GENERATE_SOURCEMAP=false
REACT_APP_DEBUG=false
```

## Domain Setup
1. Add custom domain: `goinvesting.ai`
2. Configure DNS records as instructed
3. Enable SSL certificate
4. Test the deployment

## Post-Deploy Checklist
- [ ] Site loads correctly
- [ ] Navigation works
- [ ] API calls work
- [ ] Authentication works
- [ ] PWA features work
- [ ] Performance is good
- [ ] SSL certificate is active

## Troubleshooting
- Check browser console for errors
- Verify environment variables
- Check CORS settings on backend
- Test API endpoints

---
**✅ Ready for deployment!**
