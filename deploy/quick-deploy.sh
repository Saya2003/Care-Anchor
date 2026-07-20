#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# CareAnchor — Quick Deploy Script for Alibaba Cloud ECS
# This script handles the complete deployment in one command
# ──────────────────────────────────────────────────────────────────────────────

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║         CareAnchor - Alibaba Cloud ECS Quick Deploy                    ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Get project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# ─── Step 1: Check Prerequisites ─────────────────────────────────────────────
echo "► Step 1: Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "✖ Docker not found. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    echo "✓ Docker installed"
else
    echo "✓ Docker found: $(docker --version)"
fi

if ! command -v docker-compose &> /dev/null; then
    echo "✖ Docker Compose not found. Installing..."
    apt install -y docker-compose
    echo "✓ Docker Compose installed"
else
    echo "✓ Docker Compose found: $(docker-compose --version)"
fi

if ! command -v node &> /dev/null; then
    echo "✖ Node.js not found. Installing..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y nodejs
    echo "✓ Node.js installed"
else
    echo "✓ Node.js found: $(node --version)"
fi

echo ""

# ─── Step 2: Environment Configuration ───────────────────────────────────────
echo "► Step 2: Configuring environment..."

if [ ! -f ".env" ]; then
    echo "✖ .env file not found!"
    echo "→ Create .env file with your API keys before deploying"
    echo "→ You can use: cp deploy/.env.ecs.template .env"
    echo "→ Then edit .env with your actual API keys"
    exit 1
fi

# Check for required environment variables
source .env
if [ -z "${DASHSCOPE_API_KEY:-}" ] && [ -z "${OPENROUTER_API_KEY:-}" ]; then
    echo "✖ No API key found in .env"
    echo "→ Please set DASHSCOPE_API_KEY or OPENROUTER_API_KEY in .env"
    exit 1
fi

echo "✓ Environment file configured"
echo ""

# ─── Step 3: Build Frontend ──────────────────────────────────────────────────
echo "► Step 3: Building frontend..."

if [ ! -d "node_modules" ]; then
    echo "→ Installing dependencies..."
    npm install
fi

echo "→ Building production bundle..."
npm run build

if [ ! -d "dist" ] || [ ! -f "dist/index.html" ]; then
    echo "✖ Frontend build failed - dist/ folder missing"
    exit 1
fi

echo "✓ Frontend built successfully"
echo ""

# ─── Step 4: Deploy Docker Services ──────────────────────────────────────────
echo "► Step 4: Deploying services..."

# Stop existing containers
echo "→ Stopping existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true

# Build and start services
echo "→ Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "→ Waiting for services to initialize..."
sleep 10

echo "✓ Services deployed"
echo ""

# ─── Step 5: Health Checks ───────────────────────────────────────────────────
echo "► Step 5: Running health checks..."

# Check database
DB_HEALTH=$(docker-compose exec -T db pg_isready -U postgres 2>/dev/null || echo "failed")
if [[ "$DB_HEALTH" == *"accepting connections"* ]]; then
    echo "✓ Database: healthy"
else
    echo "⚠ Database: $DB_HEALTH"
fi

# Check API
API_HEALTH=$(curl -sf http://localhost/health 2>/dev/null || echo "failed")
if [ "$API_HEALTH" = '{"status":"ok"}' ]; then
    echo "✓ API: healthy"
else
    echo "⚠ API: $API_HEALTH"
    echo "→ Check logs with: docker-compose logs api"
fi

# Check nginx
NGINX_STATUS=$(docker-compose ps nginx | grep -i "up" || echo "down")
if [[ "$NGINX_STATUS" == *"Up"* ]]; then
    echo "✓ Nginx: running"
else
    echo "⚠ Nginx: not running"
fi

echo ""

# ─── Step 6: Get Server Info ─────────────────────────────────────────────────
echo "► Step 6: Deployment information..."

# Try to get public IP
PUBLIC_IP=$(curl -sf ifconfig.me 2>/dev/null || curl -sf icanhazip.com 2>/dev/null || echo "unknown")

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                    Deployment Complete! 🚀                             ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Access your application:"
echo ""
echo "  🌐 Web Interface:   http://$PUBLIC_IP"
echo "  💚 Health Check:    http://$PUBLIC_IP/health"
echo "  🔌 WebSocket:       ws://$PUBLIC_IP/ws/chat/<session-id>"
echo "  ☁️  Alibaba Info:    http://$PUBLIC_IP/alibaba/runtime"
echo ""
echo "Useful commands:"
echo ""
echo "  View logs:          docker-compose logs -f"
echo "  View API logs:      docker-compose logs -f api"
echo "  Restart services:   docker-compose restart"
echo "  Stop services:      docker-compose down"
echo "  Update app:         git pull && ./deploy/quick-deploy.sh"
echo ""
echo "For screenshots:"
echo ""
echo "  1. ECS Console:     Show running instance with IP"
echo "  2. Terminal:        Run: curl http://$PUBLIC_IP/alibaba/runtime"
echo "  3. Browser:         Visit: http://$PUBLIC_IP"
echo ""
echo "Need help? Check DEPLOYMENT_GUIDE.md for detailed instructions."
echo ""
