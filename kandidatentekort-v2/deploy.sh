#!/bin/bash
# kandidatentekort-v2/deploy.sh
# Eén commando: secrets pushen + worker deployen
# Gebruik: bash deploy.sh

set -e

ENV_FILE="$(dirname "$0")/../.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ .env niet gevonden op: $ENV_FILE"
  exit 1
fi

# Laad .env
export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)

echo "⛅️  kandidatentekort Worker v2 — Deploy"
echo "──────────────────────────────────────"

# 1. Deploy eerst (maakt de worker aan als die nog niet bestaat)
echo ""
echo "📦 Stap 1/2 — Worker deployen..."
npx wrangler deploy

echo ""
echo "🔑 Stap 2/2 — Secrets pushen..."

# Supabase
echo "$SUPABASE_URL" | npx wrangler secret put SUPABASE_URL
echo "  ✅ SUPABASE_URL"

echo "$SUPABASE_KEY" | npx wrangler secret put SUPABASE_KEY
echo "  ✅ SUPABASE_KEY"

# Resend
echo "$RESEND_API_KEY" | npx wrangler secret put RESEND_API_KEY
echo "  ✅ RESEND_API_KEY"

# Pipedrive
echo "$PIPEDRIVE_API_TOKEN" | npx wrangler secret put PIPEDRIVE_API_TOKEN
echo "  ✅ PIPEDRIVE_API_TOKEN"

# Slack
echo "$SLACK_WEBHOOK_URL" | npx wrangler secret put SLACK_WEBHOOK_URL
echo "  ✅ SLACK_WEBHOOK_URL"

echo ""
echo "🧪 Stap 3/3 — Health check..."
WORKER_URL=$(npx wrangler deployments list --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('url',''))" 2>/dev/null || echo "")

if [ -n "$WORKER_URL" ]; then
  curl -s "$WORKER_URL/health" | python3 -m json.tool
else
  echo "  ℹ️  Worker URL: https://kandidatentekort-worker.<account>.workers.dev/health"
fi

echo ""
echo "✅ Deploy compleet! Test met:"
echo "   curl -X POST https://kandidatentekort-worker.<account>.workers.dev/webhook \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"sector\":\"automation\",\"functie\":\"PLC Programmeur\",\"bedrijf\":\"TestBV\",\"regio\":\"Gelderland\",\"email\":\"wouter@recruitin.nl\",\"naam\":\"Wouter\"}'"
