# 🚀 Quick Deploy to Alibaba Cloud ECS

**Time required:** 15-20 minutes  
**Cost:** Less than $5 for hackathon submission

---

## Step 1: Create ECS Instance (5 minutes)

### 1.1 Go to ECS Console
- Visit: https://ecs.console.aliyun.com/
- Click **"Create Instance"**

### 1.2 Configure Instance
```
Region:           Choose closest (US East, Singapore, etc.)
Instance Type:    ecs.c6.large (2 vCPU, 4GB RAM)
                  OR ecs.t5-lc1m2.small (Free tier)
Image:            Ubuntu 22.04 64-bit
Storage:          40 GB (default)
Network:          ✓ Assign Public IPv4 Address
Bandwidth:        5 Mbps minimum
```

### 1.3 Security Group
Add these rules:
```
Port 22  (SSH)   → 0.0.0.0/0
Port 80  (HTTP)  → 0.0.0.0/0
Port 443 (HTTPS) → 0.0.0.0/0
```

### 1.4 Set Password
- Choose "Password" login method
- Set a strong root password
- **Save this password!**

### 1.5 Create & Note IP
- Click "Create Instance"
- **Copy your Public IP address** (e.g., 47.89.123.456)

---

## Step 2: Get DashScope API Key (3 minutes)

### 2.1 Go to DashScope Console
- Visit: https://dashscope.console.aliyun.com/
- Sign in with Alibaba Cloud account

### 2.2 Create API Key
- Click "API Key Management"
- Create new key or copy existing
- **Save this key!** (Format: sk-ws-XXXXX...)

---

## Step 3: Deploy CareAnchor (10 minutes)

### 3.1 Connect via SSH

**Windows (PuTTY):**
```
Host: root@YOUR_PUBLIC_IP
Port: 22
```

**Mac/Linux (Terminal):**
```bash
ssh root@YOUR_PUBLIC_IP
```

### 3.2 Clone Repository
```bash
cd /root
git clone https://github.com/Saya2003/Care-Anchor.git
cd Care-Anchor
```

### 3.3 Configure Environment
```bash
# Copy template
cp deploy/.env.ecs.template .env

# Edit with your values
nano .env
```

**Required changes in .env:**
```bash
# Replace with your actual DashScope API key (from your local .env):
DASHSCOPE_API_KEY="sk-ws-YOUR_ACTUAL_DASHSCOPE_KEY"

# Replace with your actual OpenRouter API key (from your local .env):  
OPENROUTER_API_KEY="sk-or-v1-YOUR_ACTUAL_OPENROUTER_KEY"

# Set a secure database password:
POSTGRES_PASSWORD="YourSecurePassword123!"

# Replace with your ECS public IP:
VITE_API_WS_URL="ws://47.89.123.456"
CORS_ORIGINS="http://47.89.123.456,http://localhost:5173,http://localhost"
```

**Save:** Press `Ctrl+X`, then `Y`, then `Enter`

> **Security Note:** Your API keys are safely stored in .env (gitignored) and won't be committed to the repository.

### 3.4 Run One-Command Deploy
```bash
chmod +x deploy/quick-deploy.sh
./deploy/quick-deploy.sh
```

This will automatically:
- ✓ Install Docker, Docker Compose, Node.js
- ✓ Build frontend (`npm run build`)
- ✓ Start all services (PostgreSQL, FastAPI, Nginx)
- ✓ Run health checks
- ✓ Show access URLs

**Wait 2-3 minutes** for installation and build.

---

## Step 4: Verify & Test (2 minutes)

### 4.1 Check Services
```bash
# Should return: {"status":"ok"}
curl http://localhost/health

# Should return Alibaba Cloud config JSON
curl http://localhost/alibaba/runtime
```

### 4.2 Test from Browser
- Open: `http://YOUR_PUBLIC_IP`
- You should see CareAnchor login page
- Sign up and test the chat

---

## Step 5: Take Screenshots (2 minutes)

### Screenshot 1: ECS Console
- Go to https://ecs.console.aliyun.com/
- Show running instance with public IP
- **Take screenshot**

### Screenshot 2: Terminal Output
```bash
# Run these commands
docker-compose ps
curl http://YOUR_PUBLIC_IP/alibaba/runtime
curl http://YOUR_PUBLIC_IP/health
```
- **Take screenshot** of terminal showing success

### Screenshot 3: Live Application
- Open `http://YOUR_PUBLIC_IP` in browser
- Sign up and start a chat
- **Take screenshot** of chat interface

---

## Troubleshooting

### Can't SSH?
```bash
# Check Security Group has port 22 open
# Verify using correct IP address
# Try resetting password in ECS console
```

### Services won't start?
```bash
# Check logs
docker-compose logs

# Restart
docker-compose down
docker-compose up -d
```

### Can't access from browser?
```bash
# Verify Security Group has port 80 open
# Check CORS_ORIGINS in .env has your IP
# Try: http://YOUR_IP (not https)
```

### Frontend blank page?
```bash
# Rebuild frontend
npm run build

# Restart nginx
docker-compose restart nginx
```

---

## Useful Commands

```bash
# View all logs
docker-compose logs -f

# View API logs only
docker-compose logs -f api

# Restart services
docker-compose restart

# Stop everything
docker-compose down

# Update and redeploy
git pull
./deploy/quick-deploy.sh
```

---

## What You Get

After successful deployment:

- ✅ **Web Interface**: `http://YOUR_IP`
- ✅ **Health Check**: `http://YOUR_IP/health`
- ✅ **Alibaba Info**: `http://YOUR_IP/alibaba/runtime`
- ✅ **WebSocket**: `ws://YOUR_IP/ws/chat/<session-id>`
- ✅ **PostgreSQL**: Running on port 5432 (internal)
- ✅ **FastAPI**: Running on port 8000 (internal)
- ✅ **Nginx**: Reverse proxy on port 80 (public)

---

## Next Steps

1. ✓ Test all features (chat, vitals tracking, safety alerts)
2. ✓ Take required screenshots
3. ✓ Record 3-minute demo video
4. ✓ Submit to hackathon

**Need more details?** See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for comprehensive instructions.

---

## Cost Estimate

For hackathon submission (3-5 days):
- **ECS Instance**: $2-5
- **Bandwidth**: $1-2
- **DashScope API**: Variable (pay per token)
- **Total**: Under $10

---

## Support

Having issues?
- Check `docker-compose logs api` for errors
- Review `.env` file for correct API key and IP
- See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed steps
- Check Security Group allows ports 22, 80, 443

Good luck with your hackathon submission! 🚀
