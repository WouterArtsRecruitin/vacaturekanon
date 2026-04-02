#!/bin/bash
# Kandidatentekort V8 Engine — Cron wrapper
LOGFILE="/Users/wouterarts/recruitin/logs/engine.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "" >> "$LOGFILE"
echo "═══════════════════════════════════" >> "$LOGFILE"
echo "[$TIMESTAMP] Engine gestart" >> "$LOGFILE"
echo "═══════════════════════════════════" >> "$LOGFILE"

cd /Users/wouterarts/recruitin
/opt/homebrew/bin/python3 scripts/kt_engine_v8.py >> "$LOGFILE" 2>&1

EXIT_CODE=$?
echo "[$TIMESTAMP] Klaar — exit code: $EXIT_CODE" >> "$LOGFILE"
