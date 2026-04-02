#!/bin/bash
set -e
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# V2 Meta Automation Cron-Wrapper (Kandidatentekort / Metamonitor)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Draait veilig vanuit een crontab of launchd enviroment achter de schermen.

PYTHON_EXE="/opt/homebrew/bin/python3"
SCRIPT_DIR="$HOME/recruitin/scripts"
LOG_FILE="/tmp/metamonitor_cron.log"

echo "========================================" >> $LOG_FILE
echo "Start Metamonitor V2 Flow: $(date)" >> $LOG_FILE

# 1. Instagram Profile Scraper via Apify
echo "-> Starting apify_ig_sync" >> $LOG_FILE
$PYTHON_EXE "$SCRIPT_DIR/apify_ig_sync.py" >> $LOG_FILE 2>&1

# 2. Meta Marketing API synchronisatie & alerts
echo "-> Starting metamonitor_agent" >> $LOG_FILE
$PYTHON_EXE "$SCRIPT_DIR/metamonitor_agent.py" >> $LOG_FILE 2>&1

# 3. CSV is ready for Google Sheets import (all data goes directly to CSV now)
echo "-> CSV ready for Google Sheets import" >> $LOG_FILE

# 4. Meta Radar Agent (Competitor Ad Tracker via Apify)
echo "-> Starting Meta Radar Agent" >> $LOG_FILE
$PYTHON_EXE "$SCRIPT_DIR/meta_radar_agent.py" >> $LOG_FILE 2>&1

# 5. Competitor Monitor V2 (CSV-based Competitor Monitoring via Apify)
echo "-> Starting Competitor Monitor V2" >> $LOG_FILE
$PYTHON_EXE "$SCRIPT_DIR/apify_competitor_monitor_v2.py" >> $LOG_FILE 2>&1

# 6. Topic Monitor (Keyword-based Ad Library Monitor)
echo "-> Starting Topic Monitor" >> $LOG_FILE
$PYTHON_EXE "$SCRIPT_DIR/topic_monitor.py" >> $LOG_FILE 2>&1

# 7. Daily Digest (Consolidated Report @ 08:00)
HOUR=$(date +%H)
if [ "$HOUR" = "08" ]; then
    echo "-> Starting Daily Digest" >> $LOG_FILE
    $PYTHON_EXE "$SCRIPT_DIR/daily_digest.py" >> $LOG_FILE 2>&1
fi

echo "✅ Unified Monitoring Pipeline voltooid op: $(date)" >> $LOG_FILE
echo "========================================" >> $LOG_FILE
