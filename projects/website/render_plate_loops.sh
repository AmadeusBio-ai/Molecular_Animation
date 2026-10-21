#!/bin/bash
# Render the website plate loops (plate_loops.py), resumable. Each shot: build and save
# projects/website/loops/plate-<shot>.blend if it is missing, then render frames 1..N into
# renders/website/plate-loops/<shot>/<take>/ (tools/render.py skips frames that exist). Waits for MIN_FREE_GB of free
# RAM before each shot (Windows; elsewhere it does not wait). Run from anywhere, in its own console:
#   bash projects/website/render_plate_loops.sh 2>&1 | tee -a renders/plate-loops-queue.log
# Hemoglobin is take-02: take-01 was framed as its plate and its turn swung the envelope through the bottom edge.
cd "$(dirname "$0")/../.." || exit 1
MIN_FREE_GB=${MIN_FREE_GB:-10}
B=${BLENDER:-blender}
count() { if [ -d "$1" ]; then ls "$1" | grep -c '^[0-9]\{4\}\.png$'; else echo 0; fi; }
wait_for_memory() {
  command -v powershell >/dev/null || return 0
  while true; do
    free=$(powershell -NoProfile -Command "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r')
    [ "$free" -ge "$MIN_FREE_GB" ] && return
    echo "$(date '+%F %T') waiting: ${free} GB free, need ${MIN_FREE_GB} GB"; sleep 300
  done
}
for spec in nucleosome:240:take-01 hemoglobin:288:take-02 dna:288:take-01 p53dna:240:take-01 agents:240:take-01 \
            igg:240:take-01 gfp:240:take-01 kcsa:240:take-01 aquaporin:240:take-01; do
  IFS=: read -r shot n take <<< "$spec"
  out=renders/website/plate-loops/$shot; dir=$out/$take; blend=projects/website/loops/plate-$shot.blend
  mkdir -p $out
  if [ "$(count $dir)" -lt $n ]; then
    wait_for_memory
    if [ ! -f $blend ]; then
      echo "$(date '+%F %T') build $shot"
      "$B" -b --factory-startup --python projects/website/plate_loops.py -- --shot $shot --save > $out/build.log 2>&1
      grep '^RESULT' $out/build.log > $out/build-result.txt || { echo "$(date '+%F %T') STOPPED: build $shot failed"; exit 1; }
    fi
    echo "$(date '+%F %T') $shot $take from frame $(( $(count $dir) + 1 ))"
    t0=$(date +%s)
    "$B" -b $blend --python tools/render.py -- --frames 1-$n --out $dir/ >> $out/$take.log 2>&1
    echo "$(date '+%F %T') $shot: $(count $dir)/$n frames ($(( ($(date +%s) - t0) / 60 )) min)"
  fi
  [ "$(count $dir)" -ge $n ] || { echo "$(date '+%F %T') STOPPED: $dir has $(count $dir)/$n frames; see its log"; exit 1; }
done
echo "$(date '+%F %T') ALL DONE"
