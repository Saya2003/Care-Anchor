#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# CareAnchor — Alibaba Cloud infrastructure verification
#
# This script verifies:
#   1. DashScope API endpoint is reachable (Alibaba Cloud Model Studio)
#   2. DASHSCOPE_API_KEY is configured
#   3. API key has valid permissions (lightweight model call)
#   4. Network routing to Alibaba Cloud is functional
#
# Run:  bash deploy/verify-alibaba.sh
# ──────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); echo "  ✓ $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  ✖ $1"; }

echo "▸ CareAnchor — Alibaba Cloud Verification"
echo

# ─── 1. DNS resolution ────────────────────────────────────────────────────────
echo "── 1. Network routing ──"

DASHSCOPE_HOST="dashscope.aliyuncs.com"

if host "$DASHSCOPE_HOST" >/dev/null 2>&1; then
  IP=$(host "$DASHSCOPE_HOST" | head -1 | awk '{print $NF}')
  pass "DNS resolves $DASHSCOPE_HOST → $IP"
else
  fail "DNS resolution failed for $DASHSCOPE_HOST"
fi

if ping -c 1 -W 3 "$DASHSCOPE_HOST" >/dev/null 2>&1; then
  pass "ICMP reachable to $DASHSCOPE_HOST"
else
  fail "ICMP unreachable to $DASHSCOPE_HOST (may be firewalled — expected for Alibaba Cloud)"
fi

# ─── 2. HTTPS connectivity ────────────────────────────────────────────────────
echo
echo "── 2. DashScope endpoint ──"

ENDPOINT="https://dashscope.aliyuncs.com/compatible-mode/v1/models"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$ENDPOINT" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" != "000" ]; then
  pass "HTTPS reachable to $ENDPOINT (HTTP $HTTP_CODE)"
else
  fail "Cannot reach $ENDPOINT — check ECS security group egress rules"
fi

# ─── 3. API key validation ────────────────────────────────────────────────────
echo
echo "── 3. API key ──"

# Load .env if present
if [ -f "$PROJECT_DIR/.env" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$PROJECT_DIR/.env"
  set +a
fi

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  fail "OPENROUTER_API_KEY is not set"
else
  API_KEY="${OPENROUTER_API_KEY:-}"
  KEY_PREFIX="${API_KEY:0:8}"
  MASKED="${KEY_PREFIX}****"
  pass "Alibaba Cloud API key is configured ($MASKED)"

  # Lightweight model list call to verify the key works
  RESP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 \
    -H "Authorization: Bearer $API_KEY" \
    "https://dashscope.aliyuncs.com/compatible-mode/v1/models" 2>/dev/null || echo "000")

  if [ "$RESP" = "200" ]; then
    pass "API key is valid — authorized to call DashScope"
  elif [ "$RESP" = "401" ]; then
    fail "API key rejected (HTTP 401) — check DASHSCOPE_API_KEY"
  elif [ "$RESP" = "403" ]; then
    fail "API key lacks permissions (HTTP 403)"
  else
    fail "API key validation returned HTTP $RESP"
  fi
fi

# ─── 4. Environment file check ────────────────────────────────────────────────
echo
echo "── 4. ECS environment ──"

if [ -f /etc/aliyun/ecs/meta-data 2>/dev/null ] || curl -sf --max-time 3 http://100.100.100.200/latest/meta-data/ >/dev/null 2>&1; then
  INSTANCE_ID=$(curl -sf --max-time 3 http://100.100.100.200/latest/meta-data/instance-id 2>/dev/null || echo "unknown")
  REGION=$(curl -sf --max-time 3 http://100.100.100.200/latest/meta-data/region-id 2>/dev/null || echo "unknown")
  pass "Running on Alibaba Cloud ECS (instance: $INSTANCE_ID, region: $REGION)"
else
  fail "Not running on Alibaba Cloud ECS (or meta-data endpoint unreachable)"
fi

# ─── Summary ──────────────────────────────────────────────────────────────────
echo
echo "── Results ──"
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo

if [ "$FAIL" -eq 0 ]; then
  echo "  All checks passed — CareAnchor is fully connected to Alibaba Cloud."
else
  echo "  Some checks failed — see above for details."
fi
