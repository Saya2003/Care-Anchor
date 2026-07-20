# CareAnchor - Netlify Deployment Guide

## 🚀 Deploy CareAnchor to Netlify

CareAnchor is configured for deployment on Netlify with serverless functions for the backend API.

### Prerequisites

1. **Netlify Account**: Sign up at [netlify.com](https://netlify.com)
2. **GitHub Repository**: This repository at [Care-Anchor](https://github.com/Saya2003/Care-Anchor)
3. **API Keys**: Required for AI and authentication services

### 📋 Quick Deployment Steps

#### 1. Connect Repository to Netlify

1. Go to [Netlify Dashboard](https://app.netlify.com)
2. Click **"New site from Git"**
3. Choose **GitHub** and authorize Netlify
4. Select **"Saya2003/Care-Anchor"** repository
5. Configure build settings:
   - **Build command**: `npm run build`
   - **Publish directory**: `dist`
   - **Functions directory**: `netlify/functions`

#### 2. Configure Environment Variables

In Netlify Dashboard → Site Settings → Environment Variables, add:

```bash
# Authentication (Supabase)
SUPABASE_PROJECT_ID=your_project_id
SUPABASE_PUBLISHABLE_KEY=your_publishable_key
SUPABASE_URL=https://your_project_id.supabase.co
VITE_SUPABASE_PROJECT_ID=your_project_id
VITE_SUPABASE_PUBLISHABLE_KEY=your_publishable_key
VITE_SUPABASE_URL=https://your_project_id.supabase.co

# AI Configuration
DASHSCOPE_API_KEY=your_dashscope_api_key
OPENROUTER_API_KEY=your_backup_openrouter_key
QWEN_PLUS_MODEL=qwen2.5-max
QWEN_MAX_MODEL=qwen2.5-turbo

# Application Settings
CORS_ORIGINS=https://*.netlify.app
NODE_ENV=production

# WebSocket Configuration
VITE_API_WS_URL=wss://your-app-name.netlify.app

# Safety Thresholds
SYSTOLIC_BP_MAX=180
HEART_RATE_MAX=140
HEART_RATE_MIN=40
SP_O2_MIN=90
TEMPERATURE_MAX=39.5
```

#### 3. Deploy

1. Click **"Deploy site"**
2. Wait for build to complete
3. Your app will be available at `https://your-app-name.netlify.app`

### 🔧 Advanced Configuration

#### Custom Domain (Optional)

1. Go to Site Settings → Domain Management
2. Add custom domain
3. Configure DNS records as instructed

#### Build Hooks

Set up automatic deployments:
1. Site Settings → Build & Deploy → Build Hooks
2. Create webhook for automatic GitHub deployments

### 📡 API Endpoints

Once deployed, your API will be available at:

- **Health Check**: `https://your-app.netlify.app/api/health`
- **Chat Sessions**: `https://your-app.netlify.app/api/sessions`
- **Health Analytics**: `https://your-app.netlify.app/api/analytics/health-overview`
- **WebSocket**: `wss://your-app.netlify.app/ws/chat/{session_id}`

### 🔐 Required API Keys Setup

#### 1. Supabase (Authentication)
- Sign up at [supabase.com](https://supabase.com)
- Create new project
- Get credentials from Settings → API

#### 2. DashScope (Alibaba Cloud AI)
- Sign up at [DashScope Console](https://dashscope.aliyuncs.com/)
- Create API key
- Format: `sk-ws-xxxxx`

#### 3. OpenRouter (Backup AI Provider)
- Sign up at [openrouter.ai](https://openrouter.ai)
- Create API key
- Format: `sk-or-v1-xxxxx`

### ⚡ Features Available

✅ **AI Health Assistant**: Qwen 2.5 models via DashScope  
✅ **Voice Interaction**: Browser-based speech recognition  
✅ **Real-time Analytics**: Health monitoring dashboard  
✅ **Predictive Insights**: AI-powered risk assessment  
✅ **Data Export**: PDF health records generation  
✅ **Secure Chat**: Real-time WebSocket communication  
✅ **Multi-platform**: Works on desktop and mobile  

### 🔍 Troubleshooting

#### Build Failures

**Node.js Version Issues**
- Ensure Node.js 20.19+ is specified in `.nvmrc` and `netlify.toml`
- Vite requires Node.js 20.19+ or 22.12+ (Netlify default is 18.x)
- Check build logs for Node.js version errors

**Python Version Configuration Issues**
- Ensure no conflicting `runtime.txt` file exists (delete if it contains Node.js version)
- Use `python-runtime.txt` for Python serverless functions (should contain "3.11")
- Remove any `.tool-versions`, `.python-version`, or `mise.toml` files with invalid versions

**Common Build Solutions**
```bash
# Clear build cache in Netlify Dashboard
Settings → Build & Deploy → Post processing → Clear cache

# Or add to netlify.toml
[build]
  command = "npm ci && npm run build"
  environment = { NODE_VERSION = "20.19.0" }
```

**Environment Variable Issues**
- Check all required variables are set in Netlify Dashboard
- Verify API key formats (DashScope: sk-ws-*, OpenRouter: sk-or-v1-*)
- Ensure VITE_ prefixed variables are available during build

#### Function Errors
- Check Function logs in Netlify Dashboard → Functions
- Verify Python dependencies in `netlify/functions/requirements.txt`
- Test API endpoints individually: `https://your-app.netlify.app/api/health`

#### WebSocket Issues
- Ensure `VITE_API_WS_URL` uses `wss://` protocol for production
- Check browser console for WebSocket connection errors
- Verify CORS configuration in netlify.toml

#### API Integration Issues
- Test DashScope API key: `curl -H "Authorization: Bearer YOUR_KEY" https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation`
- Verify Supabase connection in browser network tab
- Check if rate limits are being hit

#### Common Solutions
```bash
# Clear build cache
netlify build --clear-cache

# Test functions locally (Netlify CLI required)
netlify dev

# Check function logs
netlify functions:logs api
```

### 📱 Production Checklist

- [ ] All environment variables configured
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active (automatic)
- [ ] API endpoints responding correctly
- [ ] WebSocket connection working
- [ ] Authentication flow tested
- [ ] Health analytics displaying data
- [ ] PDF export functioning
- [ ] Voice features working in browser

### 🎯 Performance Optimization

#### Netlify-Specific Optimizations
- **Edge Functions**: Utilized for faster response times
- **CDN**: Automatic global distribution
- **Image Optimization**: Built-in image processing
- **Split Testing**: A/B testing capabilities

#### Monitoring
- **Real User Monitoring**: Available in Pro plans
- **Analytics**: Built-in site analytics
- **Performance Metrics**: Core Web Vitals tracking

### 🚨 Important Notes

1. **WebSocket Limitations**: Netlify Functions have execution time limits. For persistent connections, consider upgrading or using external WebSocket service.

2. **Database**: SQLite works for development. For production, consider upgrading to PostgreSQL or external database service.

3. **Function Cold Starts**: First requests may be slower due to function initialization.

4. **Hackathon Compliance**: Meets all requirements for AI hackathon submissions with Alibaba Cloud integration.

### 📞 Support

For deployment issues:
1. Check [Netlify Documentation](https://docs.netlify.com)
2. Review build and function logs
3. Test API endpoints with tools like Postman
4. Verify environment variable configuration

---

**🏆 Hackathon Ready**: This configuration meets all technical requirements for AI hackathon submissions with comprehensive health monitoring capabilities and Alibaba Cloud Qwen integration.