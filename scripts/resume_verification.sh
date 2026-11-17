#!/bin/zsh
# Polite resume after Ad Library throttling: one control request, then prioritised batches,
# 1 worker + 3 s extra pause per page. Any throttle/login-wall STOP aborts the whole chain.
set -u
cd "$(dirname "$0")/.."
B=data/quality/resume_batches.json
ids() { python3 -c "import json,sys;print(' '.join(json.load(open('$B'))[sys.argv[1]]))" "$1"; }
run() {  # run <label> <verify args...>
  echo "== $1"; shift
  python3 scripts/verify_creatives.py verify --workers 1 --delay-ms 3000 "$@" 2>&1 | tee /tmp/_resume_last.log
  if grep -q '^STOP' /tmp/_resume_last.log; then echo "ABORT: throttling detected; stopping all batches"; exit 4; fi
}
echo "== control"; python3 scripts/verify_creatives.py verify --refresh --workers 1 \
   --out data/quality/control_check.json --staging-dir data/quality/control_staging 1575470834177468
python3 -c "import json,sys;d=json.load(open('data/quality/control_check.json'));sys.exit(0 if d['1575470834177468'].get('found') else 3)" \
   || { echo "CONTROL FAILED: still throttled, aborting"; exit 3; }
run "MuscleBlaze full recapture" --refresh --out data/quality/muscleblaze_recapture_cards.json \
    --staging-dir data/quality/recapture/muscleblaze $(ids mb_recapture)
run "Himalaya candidates" --out data/quality/replacement_cards.json $(ids himalaya)
run "Mamaearth spares" --out data/quality/replacement_cards.json $(ids mamaearth_spares)
run "MuscleBlaze spares" --out data/quality/replacement_cards.json $(ids mb_spares)
echo "== DONE"
