#!/bin/zsh
# One polite retry of the remaining Himalaya candidate IDs (control request first; aborts on throttle).
set -u
cd "$(dirname "$0")/.."
ids=$(python3 -c "import json;print(' '.join(json.load(open('data/quality/resume_batches.json'))['himalaya_remaining']))")
.venv/bin/python scripts/verify_creatives.py verify --refresh --workers 1 --out data/quality/control_check.json \
   --staging-dir data/quality/control_staging 1575470834177468
.venv/bin/python -c "import json,sys;sys.exit(0 if json.load(open('data/quality/control_check.json'))['1575470834177468'].get('found') else 3)" \
   || { echo "CONTROL FAILED: still throttled"; exit 3; }
.venv/bin/python scripts/verify_creatives.py verify --workers 1 --delay-ms 4000 --out data/quality/replacement_cards.json ${=ids}
