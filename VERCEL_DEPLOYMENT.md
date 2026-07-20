# CareAnchor - Vercel Deployment Guide

## Quick Deploy to Vercel

CareAnchor is configured for seamless deployment on Vercel with both frontend and serverless backend functions.

### Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Fork or clone this repository
3. **API Keys**: Obtain the required API keys (see below)

### Required Environment Variables

Set these in your Vercel dashboard under Project Settings → Environment Variables:

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

# Application Settings
CORS_ORIGINS=https://*.vercel.app
VITE_API_WS_URL=wss://your-app.vercel.app
```

### Deployment Steps

1. **Connect Repository**
   - Go to Vercel Dashboard
   - Click "New Project"
   - Import from GitHub: `https://github.com/Saya2003/Care-Anchor`

2. **Configure Build Settings**
   - Framework Preset: `Other`
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`

3. **Add Environment Variables**
   - Add all variables listed above
   - Ensure API keys are properly formatted

4. **Deploy**
   - Click "Deploy"
   - Wait for build completion
   - Your app will be available at `https://your-app.vercel.app`

### API Keys Setup

#### Supabase (Authentication)
1. Create project at [supabase.com](https://supabase.com)
2. Get Project ID and Publishable Key from Settings → API

#### DashScope (Alibaba Cloud AI)
1. Sign up at [DashScope](https://dashscope.aliyuncs.com/)
2. Create API key in console
3. Format: `sk-ws-xxxxx`

#### OpenRouter (Backup AI)
1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Create API key
3. Format: `sk-or-v1-xxxxx`

### Features Included

✅ **AI-Powered Health Assistant**: Qwen 2.5 models via DashScope  
✅ **Voice Interaction**: Speech-to-text and text-to-speech  
✅ **Health Analytics**: Real-time monitoring and insights  
✅ **Predictive Health**: AI risk assessment and recommendations  
✅ **Data Export**: PDF generation of health records  
✅ **Real-time Chat**: WebSocket-based conversations  
✅ **Secure Authentication**: Supabase integration  

### Troubleshooting

- **Build Failures**: Check environment variables format
- **API Errors**: Verify API keys and quotas
- **WebSocket Issues**: Ensure VITE_API_WS_URL uses `wss://` protocol
- **CORS Errors**: Update CORS_ORIGINS to match your domain

### Production Checklist

- [ ] All environment variables configured
- [ ] API keys have sufficient quotas
- [ ] Supabase authentication configured
- [ ] Domain configured (optional)
- [ ] SSL certificate active
- [ ] Health monitoring endpoints accessible

### Support

For deployment issues, check:
1. Vercel deployment logs
2. Browser developer console
3. API endpoint responses at `/api/health`

---

**Hackathon Ready**: This application meets all requirements for AI hackathon submissions with Alibaba Cloud integration.