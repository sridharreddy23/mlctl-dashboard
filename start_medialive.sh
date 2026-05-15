#!/bin/bash

REGION="us-east-1"

CHANNEL_ARNS=(
"arn:aws:medialive:us-east-1:149306543115:channel:2238084"
"arn:aws:medialive:us-east-1:149306543115:channel:771047"
"arn:aws:medialive:us-east-1:149306543115:channel:363722"
)

BACKUP_DIR="./input_backups"
mkdir -p "$BACKUP_DIR"

# ================= COLORS =================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date)]${NC} $1"; }
success() { echo -e "${GREEN}✔ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
error() { echo -e "${RED}✖ $1${NC}"; }

# ================= UTIL =================

extract_channel_id() {
  echo "$1" | awk -F: '{print $NF}'
}

run_cmd() {
  OUTPUT=$("$@" 2>&1)
  STATUS=$?

  if [ $STATUS -ne 0 ]; then
    error "$OUTPUT"
    return 1
  fi
  return 0
}

get_input_id() {
  aws medialive describe-channel \
    --channel-id "$1" \
    --region "$REGION" \
    --query 'InputAttachments[0].InputId' \
    --output text
}

get_current_url() {
  aws medialive describe-input \
    --input-id "$1" \
    --region "$REGION" \
    --query 'Sources[0].Url' \
    --output text
}

backup_url() {
  FILE="$BACKUP_DIR/${1}_latest.txt"
  echo "$2" > "$FILE"
  success "Backup saved → $FILE"
}

precheck_hls() {
  URL=$1

  log "Prechecking HLS URL..."

  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
  if [ "$HTTP_STATUS" != "200" ]; then
    error "HLS not reachable (HTTP $HTTP_STATUS)"
    return 1
  fi

  if ! curl -s "$URL" | grep -q "#EXTM3U"; then
    error "Invalid HLS playlist"
    return 1
  fi

  success "HLS URL looks valid"
}

wait_for_running() {
  CHANNEL_ID=$1

  for i in {1..30}; do
    STATE=$(aws medialive describe-channel \
      --channel-id "$CHANNEL_ID" \
      --region "$REGION" \
      --query 'State' \
      --output text)

    log "State: $STATE (waiting for RUNNING)"
    [ "$STATE" = "RUNNING" ] && return 0
    sleep 5
  done

  warn "Channel did not reach RUNNING in time"
  return 1
}

# ================= USER INPUT =================

echo -e "\nSelect Channel:"
for i in "${!CHANNEL_ARNS[@]}"; do
  echo "$((i+1))) ${CHANNEL_ARNS[$i]}"
done

read -p "Enter choice (1-3): " CHOICE
[[ ! "$CHOICE" =~ ^[1-3]$ ]] && { error "Invalid choice"; exit 1; }

SELECTED_ARN=${CHANNEL_ARNS[$((CHOICE-1))]}
CHANNEL_ID=$(extract_channel_id "$SELECTED_ARN")

echo ""
echo "1) Update to NEW URL"
echo "2) Rollback to LAST URL"
read -p "Choose option (1-2): " MODE

if [ "$MODE" = "1" ]; then
  read -p "Enter new HLS URL: " TARGET_URL
  [ -z "$TARGET_URL" ] && { error "No URL provided"; exit 1; }

  precheck_hls "$TARGET_URL" || exit 1

elif [ "$MODE" = "2" ]; then
  FILE="$BACKUP_DIR/${CHANNEL_ID}_latest.txt"

  if [ ! -f "$FILE" ]; then
    error "No backup found!"
    exit 1
  fi

  TARGET_URL=$(cat "$FILE")
  warn "Rolling back to: $TARGET_URL"

else
  error "Invalid option"
  exit 1
fi

# ================= MAIN =================

log "Processing Channel: $CHANNEL_ID"

INPUT_ID=$(get_input_id "$CHANNEL_ID")
if [ -z "$INPUT_ID" ] || [ "$INPUT_ID" = "None" ]; then
  error "No input found"
  exit 1
fi

CURRENT_URL=$(get_current_url "$INPUT_ID")
log "Current URL: $CURRENT_URL"

if [ "$CURRENT_URL" = "$TARGET_URL" ]; then
  warn "URL already same. Exiting."
  exit 0
fi

backup_url "$CHANNEL_ID" "$CURRENT_URL"

STATE=$(aws medialive describe-channel \
  --channel-id "$CHANNEL_ID" \
  --region "$REGION" \
  --query 'State' \
  --output text)

log "Current state: $STATE"

# ================= STOP =================

if [ "$STATE" = "RUNNING" ]; then
  log "Stopping channel..."
  run_cmd aws medialive stop-channel \
    --channel-id "$CHANNEL_ID" \
    --region "$REGION"
fi

# ================= WAIT FOR IDLE (WITH TIMEOUT) =================

log "Waiting for IDLE (max 2 min)..."

MAX_WAIT=120
INTERVAL=5
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
  STATE=$(aws medialive describe-channel \
    --channel-id "$CHANNEL_ID" \
    --region "$REGION" \
    --query 'State' \
    --output text)

  log "State: $STATE"

  [ "$STATE" = "IDLE" ] && break

  sleep $INTERVAL
  ELAPSED=$((ELAPSED + INTERVAL))
done

# ================= UPDATE WITH RETRY =================

log "Updating input (retry mode)..."

UPDATED=false

for i in {1..12}; do
  OUTPUT=$(aws medialive update-input \
    --input-id "$INPUT_ID" \
    --sources Url="$TARGET_URL" \
    --region "$REGION" 2>&1)

  STATUS=$?

  if [ $STATUS -eq 0 ]; then
    success "Input updated"
    UPDATED=true
    break
  fi

  if echo "$OUTPUT" | grep -q "ConflictException"; then
    warn "Channel still stopping, retry $i..."
    sleep 10
    continue
  fi

  error "$OUTPUT"
  exit 1
done

[ "$UPDATED" = false ] && { error "Failed to update input"; exit 1; }

# ================= START =================

log "Starting channel..."
run_cmd aws medialive start-channel \
  --channel-id "$CHANNEL_ID" \
  --region "$REGION"

wait_for_running "$CHANNEL_ID"

success "🎉 Channel RUNNING with new input"
