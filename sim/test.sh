#!/bin/sh
# Runs the five-board Rivanna3S car (prebuilt stripped ELFs in sim/fw) for 10 virtual seconds on one CAN bus.
# Pass means: all five boards booted, BPS status frames (0x406) reached the bus, the BPS weak-cell fault
# at 8 s was seen by the boards, RelayBoard disabled precharge because of it, and no HardFault/panic occurred.
cd "$(dirname "$0")/.." || exit 1
SIM=${SIM:-sim}
O=$(mktemp -d); trap 'rm -rf "$O"' EXIT
"$SIM" run --scenario sim/scenario.yaml --timeout 10 --ascii --frames "$O/frames.txt" > "$O/uart.log" 2> "$O/sim.log" || { echo "FAIL sim exit"; exit 1; }
rc=0
chk() { if grep -a -F -q -- "$2" "$3"; then echo "ok   $1"; else echo "FAIL $1"; rc=1; fi; }
chk "TopDist booted"    "Top Dist Board initialized" "$O/uart.log"
chk "BottomDist booted" "Bottom Distance Board initialized" "$O/uart.log"
chk "Relay booted"      "Relay Board initialized" "$O/uart.log"
chk "Motor booted"      "Motor Board initialized" "$O/uart.log"
chk "Telemetry booted"  "Telemetry Board starting up" "$O/uart.log"
chk "BPS status frames on bus" "CAN Rx id=0x406" "$O/frames.txt"
chk "BPS weak-cell fault sent" "weak_cell_fault" "$O/sim.log"
chk "Relay disabled precharge on fault" "Precharge disabled due to fault" "$O/uart.log"
if grep -a -i -E "hardfault|panic|guru" "$O/uart.log" "$O/sim.log" | grep -q .; then echo "FAIL fault/panic seen"; rc=1; else echo "ok   no HardFault/panic"; fi
exit $rc
