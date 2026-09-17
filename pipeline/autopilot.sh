#!/usr/bin/env bash
# Unattended completion of the dataset. Each phase is resumable: run_dock and
# dock_analogs skip work that is already recorded, so re-running after an
# interruption picks up where it stopped.
set -u
cd "$(dirname "$0")"
PY=/home/jsemelak/Programs/mambaforge/envs/black/bin/python
export PATH=/home/jsemelak/Programs/mambaforge/envs/black/bin:$PATH
log(){ echo "[$(date +%H:%M:%S)] $*"; }

log "PHASE 1/5  conserved-water setup, HIV-1 protease"
for k in 1 2; do $PY -u run_dock.py --setups water --shard $k/2 --cpu 9 --min-free-gb 3 & done; wait

log "PHASE 2/5  deep + loose (exhaustiveness 32)"
for k in 1 2 3; do $PY -u run_dock.py --setups deep loose --shard $k/3 --cpu 6 --min-free-gb 3 & done; wait

log "PHASE 3/5  blind docking, whole protein"
# two at a time: a whole-protein box builds about a gigabyte of grid maps
for k in 1 2; do $PY -u run_dock.py --setups blind --shard $k/2 --cpu 9 --min-free-gb 3 & done; wait

log "PHASE 4/5  96 design analogs"
$PY -u dock_analogs.py --cpu 20

log "PHASE 5/5  rebuild data.json"
$PY -u build_data.py --multi
log "DONE"
