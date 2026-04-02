#!/bin/bash
# Kandidatentekort Pipeline Cron Runner
# Elke 15 minuten via launchd
# Log: /tmp/kt_pipeline.log

LOG="/tmp/kt_pipeline.log"
PYTHON="/usr/bin/env python3"
BASE="/Users/wouterarts/recruitin"

echo "$(date '+%Y-%m-%d %H:%M:%S') — KT Pipeline start" >> "$LOG"

# Stap 1: V8 Unified Automation Engine 🚀
# Verwerkt AI + HTML Rapporten ZONDER ROI + Pipedrive + Lemlist
$PYTHON "$BASE/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/scripts/kt_engine_v8.py" >> "$LOG" 2>&1
echo "$(date '+%Y-%m-%d %H:%M:%S') — V8 Engine run voltooid" >> "$LOG"

echo "---" >> "$LOG"
