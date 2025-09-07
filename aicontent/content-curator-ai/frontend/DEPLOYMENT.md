# Frontend Deployment Guide
# AI Content Orchestrator Frontend

## 🚀 Production Deployment

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Vercel account
- Domain configured (goinvesting.ai)

### Environment Variables

Create `.env.production` file with:

```bash
# API Configuration
REACT_APP_API_URL=https://goinvesting.ai
REACT_APP_API_BASE_URL=https://goinvesting.ai/api/v1
REACT_APP_WS_URL=wss://goinvesting.ai/ws

# Authentication
REACT_APP_JWT_STORAGE_KEY=ai_content_orchestrator_token
REACT_APP_REFRESH_TOKEN_KEY=ai_content_orchestrator_refresh_token

# Application Settings
REACT_APP_APP_NAME=AI Content Orchestrator
REACT_APP_APP_VERSION=1.0.0
REACT_APP_ENVIRONMENT=production

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_ERROR_REPORTING=true
REACT_APP_ENABLE_PWA=true

# Billing
REACT_APP_BILLING_ENABLED=true
REACT_APP_YOOKASSA_SHOP_ID=1134145

# Performance
REACT_APP_ENABLE_SERVICE_WORKER=true
REACT_APP_CACHE_VERSION=1.0.0

# Production flags
GENERATE_SOURCEMAP=false
REACT_APP_DEBUG=false
```

### Local Build Test

```bash
# Install dependencies
npm install

# Build for production
npm run build

# Test production build locally
npm run preview
```

### Vercel Deployment

#### Option 1: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from frontend directory
cd frontend
vercel --prod

# Set environment variables
vercel env add REACT_APP_API_URL
vercel env add REACT_APP_API_BASE_URL
# ... add all environment variables
```

#### Option 2: Vercel Dashboard

1. Connect GitHub repository to Vercel
2. Set build command: `npm run build`
3. Set output directory: `build`
4. Add environment variables in dashboard
5. Deploy

### Domain Configuration

1. **Custom Domain Setup:**
   - Add `goinvesting.ai` in Vercel dashboard
   - Configure DNS records as instructed by Vercel
   - Enable SSL certificate

2. **Subdomain Setup (optional):**
   - `app.goinvesting.ai` for main application
   - `admin.goinvesting.ai` for admin panel

### Performance Optimization

#### Bundle Analysis
```bash
npm run build:analyze
```

#### PWA Features
- Service Worker for offline support
- App manifest for installability
- Push notifications support
- Background sync

#### Caching Strategy
- Static assets: 1 year cache
- API responses: 5 minutes cache
- HTML pages: No cache (SPA routing)

### Security Headers

Configured in `vercel.json`:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: camera=(), microphone=(), geolocation=()

### Error Handling

- Error Boundary for React errors
- Service Worker for network errors
- Sentry integration for error reporting
- Custom error logging endpoint

### Monitoring

#### Analytics
- Google Analytics integration
- Custom event tracking
- Performance monitoring

#### Error Reporting
- Sentry for error tracking
- Custom error endpoint
- User feedback collection

### Testing

```bash
# Run tests
npm test

# Run linting
npm run lint

# Fix linting issues
npm run lint:fix
```

### Rollback Strategy

1. **Vercel Rollback:**
   - Go to Vercel dashboard
   - Select deployment
   - Click "Promote to Production"

2. **Emergency Rollback:**
   - Revert to previous commit
   - Trigger new deployment
   - Update DNS if needed

### Troubleshooting

#### Common Issues

1. **Build Failures:**
   - Check Node.js version (18+)
   - Clear node_modules and reinstall
   - Check environment variables

2. **Runtime Errors:**
   - Check browser console
   - Verify API endpoints
   - Check CORS configuration

3. **Performance Issues:**
   - Run bundle analysis
   - Check network tab
   - Optimize images and assets

#### Debug Mode

Enable debug mode in production:
```bash
REACT_APP_DEBUG=true
```

### Maintenance

#### Regular Tasks
- Update dependencies monthly
- Monitor error rates
- Check performance metrics
- Review security headers

#### Updates
- Test in staging environment
- Deploy during low traffic
- Monitor post-deployment
- Have rollback plan ready

### Support

- **Documentation:** [Frontend README](./README.md)
- **Issues:** GitHub Issues
- **Monitoring:** Vercel Analytics + Sentry
- **Performance:** Lighthouse CI

---

## 📊 Deployment Checklist

- [ ] Environment variables configured
- [ ] Build passes locally
- [ ] Tests pass
- [ ] Linting passes
- [ ] Bundle size optimized
- [ ] PWA features working
- [ ] Error boundary tested
- [ ] Service worker registered
- [ ] Domain configured
- [ ] SSL certificate active
- [ ] Analytics configured
- [ ] Error reporting active
- [ ] Performance monitoring
- [ ] Rollback plan ready

**✅ Ready for Production Deployment!**
