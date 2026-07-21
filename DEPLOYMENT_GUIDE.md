# CareAnchor - Alibaba Cloud ECS Deployment Guide

## Overview

This guide walks you through deploying CareAnchor to Alibaba Cloud ECS for the hackathon submission.

## Prerequisites

- Alibaba Cloud account
- Credit card for ECS instance (free tier available)
- SSH client (PuTTY for Windows, Terminal for Mac/Linux)
- Your Alibaba Cloud DashScope API key

## Step 1: Create Alibaba Cloud Account

1. Go to https://www.alibabacloud.com/
2. Click "Free Account" and sign up
3. Complete verification with your phone number
4. Add payment method (required even for free tier)

## Step 2: Get DashScope API Key

1. Go to https://dashscope.console.aliyun.com/
2. Sign in with your Alibaba Cloud account
3. Click "API Key Management"
4. Create a new API key or copy existing one
5. **Save this key** - you'll need it later

## Step 3: Create ECS Instance

1. Log in to Alibaba Cloud Console: https://ecs.console.aliyun.com/
2. Click "Create Instance"
3. **Region**: Choose closest to you (e.g., US East, Singapore)
4. **Instance Type**: 
   - Select "Compute Optimized" → `ecs.c6.large` (2 vCPU, 4 GB RAM)
   - Or use free tier: `ecs.t5-lc1m2.small` (1 vCPU, 2 GB RAM)
5. **Image**: Ubuntu 22.04 64-bit
6. **Storage**: 40 GB system disk (default)
7. **Network**:
   - VPC: Use default or create new
   - Public IP: **Assign Public IPv4 Address**
   - Bandwidth: 5 Mbps (minimum)
8. **Security Group**:
   - Create new security group
   - Add rules:
     - HTTP (Port 80) - Allow 0.0.0.0/0
     - HTTPS (Port 443) - Allow 0.0.0.0/0
     - SSH (Port 22) - Allow 0.0.0.0/0 (or your IP only for security)
9. **Login Credentials**:
   - Select "Password"
   - Set a strong root password
   - **Save this password**
10. Click "Create Instance"
11. **Note your Public IP address** - you'll need this

## Step 4: Connect to ECS Instance

### Windows (using PuTTY)
1. Download PuTTY: https://www.putty.org/
2. Open PuTTY
3. Host Name: `root@YOUR_PUBLIC_IP`
4. Port: 22
5. Click "Open"
6. Enter your root password

### Mac/Linux (using Terminal)
```bash
ssh root@YOUR_PUBLIC_IP
# Enter your root password when prompted
```

## Step 5: Install Prerequisites on ECS

Once connected via SSH, run these commands:

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# Install Docker Compose
apt install docker-compose -y

# Install Git
apt install git -y

# Install Node.js and npm (for frontend build)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Verify installations
docker --version
docker-compose --version
git --version
node --version
npm --version
```

## Step 6: Clone Repository and Setup

```bash
# Clone the repository
cd /root
git clone https://github.com/Saya2003/Care-Anchor.git
cd Care-Anchor

# Create .env file
cp .env .env.backup
```

Now edit the `.env` file with your settings:

```bash
nano .env
```

Update these critical values:
- `OPENROUTER_API_KEY` - Your OpenRouter API key for Codex/GPT-5.6
- `DASHSCOPE_API_KEY` - Optional, for image analysis fallback
- `DATABASE_URL` - Keep as: `postgresql+asyncpg://postgres:postgres@db:5432/careanchor`
- `POSTGRES_PASSWORD` - Change to a secure password
- `CORS_ORIGINS` - Add your ECS public IP: `http://YOUR_PUBLIC_IP,http://localhost:5173`
- `VITE_API_WS_URL` - Set to: `ws://YOUR_PUBLIC_IP`

Save and exit (Ctrl+X, then Y, then Enter)

## Step 7: Build Frontend

```bash
# Install frontend dependencies
npm install

# Build production frontend
npm run build

# Verify dist/ folder was created
ls -la dist/
```

## Step 8: Deploy with Docker Compose

```bash
# Make setup script executable
chmod +x deploy/ecs-setup.sh

# Run deployment
docker-compose up -d

# Check if containers are running
docker-compose ps

# View logs
docker-compose logs -f
```

Wait 1-2 minutes for all services to start.

## Step 9: Verify Deployment

```bash
# Test health endpoint
curl http://localhost/health
# Should return: {"status":"ok"}

# Test Alibaba Cloud connectivity
curl http://localhost/alibaba/runtime
# Should return JSON with Alibaba Cloud config

# Check from external network
curl http://YOUR_PUBLIC_IP/health
```

Visit in browser: `http://YOUR_PUBLIC_IP`

## Step 10: Take Screenshots for Submission

### Screenshot 1: ECS Console
1. Go to https://ecs.console.aliyun.com/
2. Show your running instance with public IP
3. Take screenshot

### Screenshot 2: Application Running
```bash
# Show Docker containers
docker-compose ps

# Show Alibaba Cloud runtime
curl http://YOUR_PUBLIC_IP/alibaba/runtime | jq

# Show logs with AI model mentions
docker-compose logs api | grep -i "codex\|gpt\|openrouter" | tail -20
```

Take screenshot of terminal showing these commands and their output.

### Screenshot 3: Live Application
1. Open browser: `http://YOUR_PUBLIC_IP`
2. Sign up for an account
3. Start a chat conversation
4. Take screenshot showing the interface working

## Troubleshooting

### Issue: Can't connect to ECS via SSH
- Check Security Group allows port 22
- Verify you're using correct IP address
- Try resetting instance password in ECS console

### Issue: Docker containers won't start
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d
```

### Issue: Frontend shows blank page
```bash
# Rebuild frontend
npm run build

# Restart nginx
docker-compose restart nginx
```

### Issue: Backend can't connect to database
```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Issue: Can't access from browser
- Check Security Group allows ports 80 and 443
- Check CORS_ORIGINS in .env includes your public IP
- Try accessing with http:// (not https://)

## Updating the Application

```bash
# Pull latest changes
git pull origin main

# Rebuild frontend
npm run build

# Restart services
docker-compose down
docker-compose up -d --build
```

## Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes database)
docker-compose down -v
```

## Cost Estimates

- **ECS Instance** (ecs.t5-lc1m2.small): ~$5-10/month
- **Bandwidth**: ~$0.12/GB
- **DashScope API**: Pay per token (check pricing)

**For hackathon**: A few days should cost less than $5 total.

## Security Recommendations

For production use:
1. Use HTTPS with SSL certificate
2. Restrict SSH to your IP only
3. Use stronger database passwords
4. Enable firewall rules
5. Regular security updates
6. Use IAM roles instead of API keys

## Support

If you encounter issues:
1. Check `docker-compose logs api`
2. Check `docker-compose logs db`
3. Check `docker-compose logs nginx`
4. Review error messages carefully

## Next Steps

After successful deployment:
1. ✅ Take required screenshots
2. ✅ Test all features thoroughly
3. ✅ Record 3-minute demo video
4. ✅ Submit to hackathon platform

Good luck! 🚀
