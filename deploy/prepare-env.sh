#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# CareAnchor — Prepare .env file for ECS deployment
# This script copies API keys from local .env to ECS template
# ──────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "► Preparing .env for ECS deployment..."

# Check if local .env exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "✖ No .env file found in project root"
    echo "→ Please create .env file first"
    exit 1
fi

# Source the local .env file to get variables
set -a
source "$PROJECT_DIR/.env"
set +a

# Create ECS .env file from template
cp "$SCRIPT_DIR/.env.ecs.template" "$PROJECT_DIR/.env.ecs"

# Replace placeholder values with actual values from local .env
if [ -n "${OPENROUTER_API_KEY:-}" ]; then
    sed -i "s/sk-or-v1-YOUR_OPENROUTER_API_KEY_HERE/${OPENROUTER_API_KEY}/g" "$PROJECT_DIR/.env.ecs"
    echo "✓ OpenRouter API key updated"
fi

if [ -n "${DASHSCOPE_API_KEY:-}" ]; then
    sed -i "s/YOUR_DASHSCOPE_API_KEY_HERE/${DASHSCOPE_API_KEY}/g" "$PROJECT_DIR/.env.ecs"
    echo "✓ DashScope API key updated"
fi

# Set a default secure password for PostgreSQL
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-CareAnchor$(date +%s)!}"
sed -i "s/YOUR_SECURE_PASSWORD/${POSTGRES_PASSWORD}/g" "$PROJECT_DIR/.env.ecs"
echo "✓ PostgreSQL password set"

echo ""
echo "✓ ECS environment file created: .env.ecs"
echo ""
echo "Next steps:"
echo "1. Copy .env.ecs to your ECS instance"
echo "2. Edit VITE_API_WS_URL and CORS_ORIGINS with your ECS IP"
echo "3. Rename to .env on ECS instance"
echo ""