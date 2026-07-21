#!/usr/bin/env bash
set -euo pipefail
# shellcheck disable=SC1091

# ──────────────────────────────────────────────────────────────────────────────
# CareAnchor — ECS bootstrap script
# Usage:
#   chmod +x deploy/ecs-setup.sh
#   ./deploy/ecs-setup.sh                    # guided setup
#   ALIYUN_ACCESS_KEY=xxx ./deploy/ecs-setup.sh --non-interactive
# ──────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "▸ CareAnchor ECS Bootstrap"
echo "▸ Project root: $PROJECT_DIR"

# ─── 1. Prerequisites ─────────────────────────────────────────────────────────
echo
echo "── Checking prerequisites ──"

command -v docker >/dev/null 2>&1 || { echo "✖ docker not found"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || {
  echo "✖ docker compose plugin not found; trying docker compose"
  docker compose version >/dev/null 2>&1 || { echo "✖ neither docker-compose nor docker compose available"; exit 1; }
  COMPOSE="docker compose"
}
echo "  ✓ docker: $(docker --version)"
echo "  ✓ compose: available"

# ─── 2. Environment ───────────────────────────────────────────────────────────
echo
echo "── Environment variables ──"

ENV_FILE="$PROJECT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "  ✖ .env file not found at $ENV_FILE"
  echo "  → Creating from template"
  cat > "$ENV_FILE" <<-ENVEOF
# Required: OpenRouter for AI models
OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"

# Optional: DashScope for image analysis fallback  
DASHSCOPE_API_KEY="${ALIYUN_DASHSCOPE_API_KEY:-}"

# Required: PostgreSQL (Docker Compose default)
DATABASE_URL="postgresql+asyncpg://postgres:postgres@db:5432/careanchor"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"

# Optional: safety alert webhook
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-}"

# CORS — local dev + ECS public IP
CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:5173,http://localhost}"
ENVEOF
  echo "  ✓ .env created — edit it with your DASHSCOPE_API_KEY before deploying"
else
  echo "  ✓ .env exists"
fi

# ─── 3. Build ─────────────────────────────────────────────────────────────────
echo
echo "── Building Docker images ──"

cd "$PROJECT_DIR"
docker compose build api

# ─── 4. Deploy ─────────────────────────────────────────────────────────────────
echo
echo "── Starting services ──"

# Stop existing first
docker compose down --remove-orphans 2>/dev/null || true

docker compose up -d

echo
echo "── Checking health ──"
sleep 5

HEALTH=$(curl -sf http://localhost:80/health 2>/dev/null || curl -sf http://localhost:8000/health 2>/dev/null || echo "unreachable")
if [ "$HEALTH" = '{"status":"ok"}' ]; then
  echo "  ✓ API is healthy"
else
  echo "  ⚠ Health check returned: $HEALTH"
  echo "  → Run 'docker compose logs api' to investigate"
fi

# ─── 5. Alibaba Cloud verification ────────────────────────────────────────────
echo
echo "── Alibaba Cloud connectivity ──"

if bash "$SCRIPT_DIR/verify-alibaba.sh" 2>/dev/null; then
  echo "  ✓ DashScope endpoint reachable"
else
  echo "  ⚠ DashScope connectivity check skipped (set DASHSCOPE_API_KEY to verify)"
fi

echo
echo "── Done ──"
echo "  API:        http://$(curl -sf ifconfig.me 2>/dev/null || echo 'localhost')"
echo "  Health:     http://localhost/health"
echo "  WebSocket:  ws://<host>/ws/chat/<session-id>"
echo
echo "  Next steps:"
echo "  1. Set DASHSCOPE_API_KEY in .env"
echo "  2. docker compose restart api"
echo "  3. Run deploy/verify-alibaba.sh to confirm connectivity"
