#!/usr/bin/env bash
# Arranca (o reinicia) el servidor de waitlist en una screen session. Se ejecuta EN EL SERVIDOR.
set -euo pipefail
cd "$(dirname "$0")"

screen -S idealisto-waitlist -X quit 2>/dev/null || true
sleep 1
screen -dmS idealisto-waitlist bash -c 'PORT=3201 ~/.bun/bin/bun server/index.ts 2>&1 | tee -a ~/idealisto/waitlist.log'
sleep 2
curl -sf http://localhost:3201/health && echo " — waitlist OK en :3201"
