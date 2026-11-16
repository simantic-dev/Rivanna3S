#!/bin/sh
# Runs the five-board car (sim/scenario.yaml) for N virtual seconds (default 10).
# Run from anywhere; needs `sim` on PATH (or SIM=...) and the images from sim/build.sh.
# Output: sim/out/uart.log (the boards' own log lines) and sim/out/can-frames.txt.
set -e
cd "$(dirname "$0")/.."
SIM=${SIM:-sim}
SCENARIO=${SCENARIO:-sim/scenario.yaml}
[ -f sim/build/bin/RelayBoard.elf ] || { echo "build first: sim/build.sh"; exit 1; }
mkdir -p sim/out
"$SIM" run --scenario "$SCENARIO" --timeout "${1:-10}" --ascii --frames sim/out/can-frames.txt \
  > sim/out/uart.log 2> sim/out/sim.log
grep -a -E "Precharge|SD:|bit_rate" sim/out/uart.log sim/out/sim.log | cut -c1-200 | head -20
echo "log: sim/out/uart.log   CAN frames: sim/out/can-frames.txt   (sim/out/sim.log has warnings and timing)"
