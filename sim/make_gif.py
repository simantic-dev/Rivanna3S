"""Builds sim/screenshots/car.gif from a run of sim/run.sh (sim/out/*). Pillow + ffmpeg only.
Decoding uses the team's own Common/can_structs via sim/decode_can.c.
usage: sim/make_gif.py <sim-version>      (run from the repository root, after sim/run.sh)"""
import re, subprocess, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from gifkit import *

VER = sys.argv[1]
S = Common = "Common/can_structs"
os.makedirs("sim/out", exist_ok=True)
subprocess.run(["cc", "-w", f"-I{S}/Inc", "-o", "sim/out/dec", "sim/decode_can.c", f"{S}/Src/rivanna3_s.c", f"{S}/Src/bps.c", f"{S}/Src/mppt.c"], check=True)
raw = []
for l in open("sim/out/can-frames.txt", errors="replace"):
    m = re.match(r"\[(\w+)\] \[([\d.]+)s\] \(can\d\) CAN Tx id=0x([0-9A-F]+) dlc=\d+ data=(.*)", l)
    if m: raw.append(f"{m[2]} {m[3]} {m[4]}\n")
ev = []   # (t, id, name, {field: value})
for l in subprocess.run(["sim/out/dec"], input="".join(raw), capture_output=True, text=True).stdout.splitlines():
    p = l.split(" ")
    if len(p) > 3: ev.append((float(p[0]), int(p[1], 16), p[2], {k: float(v) if re.fullmatch(r"-?[\d.]+", v) else v for k, v in (x.split("=") for x in p[3:])}))

log, last600 = [], None
for l in open("sim/out/uart.log", errors="replace"):
    m = re.match(r"\[(\w+)\] \[([\d.]+)s\] \((\w+)\) \S+ (\w+) \S*?(?:fork-rivanna3s-gif2/)?(\S+?\.\w+:\d+): (.*)", l)
    if not m or m[3] == "usart2": continue
    b, t, lv, src, msg = m[1], float(m[2]), m[4], m[5].split("/")[-1], m[6].strip()
    if lv == "DEBUG":
        if b == "relay" and "Sent CAN message with ID 600" in msg and msg != last600:
            last600 = msg; log.append((t, "INFO", f"{b}: {msg.replace('CanInterface: ', '')}"[:110]))
        continue
    if "can.cpp" in src: continue
    log.append((t, lv, f"{b}: {src} {msg}"[:110]))
log.sort()

def at(i, t):
    r = [e for e in ev if e[1] == i and e[0] <= t]
    return r[-1] if r else None

STAGES = ["WaitForHV", "WaitForEnable", "WaitForThreshold", "WaitForMainRelay", "Done", "FAULT"]
pre = [e for e in ev if e[1] == 0x258]
times = [None] * 6
for t, _, _, f in pre:
    for i in range(5):
        if f["motor_stage"] >= i and times[i] is None and f["other_fault"] == 0 and (i == 0 or f["motor_stage"] == i): times[i] = t
    if f["other_fault"] and times[5] is None: times[5] = t
MSG = [(0x406, "BpsStatus", lambda f: f"{f['pack_voltage']:.1f} V  {f['pack_current']:.1f} A  SoC {f['soc']:.0f}%"),
       (0x3AA, "BpsError", lambda f: "fault byte0=0x02 (weak cell)" if f["raw"] in (2000000, "02000000") else "no fault"),
       (0x258, "PrechargeStatus", lambda f: (f"stage {STAGES[int(f['motor_stage'])]}" if f["motor_stage"] == f["mppt_stage"] else f"motor {STAGES[int(f['motor_stage'])]}, mppt {STAGES[int(f['mppt_stage'])]}") + ( ", OTHER FAULT" if f["other_fault"] else "")),
       (0xC8, "MotorCommands", lambda f: f"throttle {f['throttle']:.0f}  regen {f['regen_braking']:.0f}  manual drive {'on' if f['manual'] else 'OFF'}"),
       (0x1F4, "PedalStatus", lambda f: f"throttle pedal {f['throttle_pedal']:.0f}  brake pedal {f['brake_pedal']:.0f}"),
       (0x180, "MPPT0 Status", lambda f: f"{f['input_current']:.2f} A in at {f['input_voltage']:.1f} V"),
       (0x181, "MPPT1 Status", lambda f: f"{f['input_current']:.2f} A in at {f['input_voltage']:.1f} V"),
       (0x280, "MPPT0 Output", lambda f: f"{f['output_voltage']:.0f} V out, {f['input_power']:.1f} W in"),
       (0x281, "MPPT1 Output", lambda f: f"{f['output_voltage']:.0f} V out, {f['input_power']:.1f} W in"),
       (0x480, "MPPT0 Temp", lambda f: f"board {f['pcb']:.0f} C, mosfet {f['mosfet']:.0f} C")]
bps = [(e[0], e[3]) for e in ev if e[1] == 0x406]

def draw(c, t):
    c.header("UVA Solar Car: five STM32G474 boards on one CAN bus", "team firmware, unmodified. Values are decoded from the CAN frames the boards transmit, with the team's own message definitions.", t)
    b = at(0x406, t); p = at(0x258, t); mc = at(0xC8, t); m0, m1 = at(0x280, t), at(0x281, t)
    tw = 196; X = [24 + i * (tw + 12) for i in range(6)]
    fault = p and p[3]["other_fault"]
    c.tile(X[0], 90, tw, 92, "PACK VOLTAGE (BMS)", f"{b[3]['pack_voltage']:.1f}" if b else "--", "V", CYAN)
    c.tile(X[1], 90, tw, 92, "PACK CURRENT", f"{b[3]['pack_current']:.1f}" if b else "--", "A", CYAN)
    c.tile(X[2], 90, tw, 92, "STATE OF CHARGE", f"{b[3]['soc']:.0f}" if b else "--", "%", GREEN)
    c.tile(X[3], 90, tw, 92, "MPPT INPUT POWER", f"{m0[3]['input_power'] + m1[3]['input_power']:.0f}" if m0 and m1 else "--", "W", AMBER)
    c.tile(X[4], 90, tw, 92, "DRIVE ENABLED", ("YES" if mc[3]["manual"] else "NO") if mc else "--", "", GREEN if mc and mc[3]["manual"] else RED)
    c.tile(X[5], 90, tw, 92, "THROTTLE PEDAL", f"{at(0x1F4, t)[3]['throttle_pedal']:.0f}" if at(0x1F4, t) else "--", "(idle)", FG)
    c.panel(24, 196, 1232, 112, "RelayBoard precharge state machine: when each state was entered")
    act = 5 if fault else (int(p[3]["motor_stage"]) if p else None)
    c.chain(40, 226, 1200, 70, STAGES, act, [x if (x is not None and x <= t) else None for x in times], [BLUE, BLUE, AMBER, AMBER, GREEN, RED])
    c.panel(24, 322, 500, 360, "CAN bus, decoded by message name")
    for i, (mid, nm, fn) in enumerate(MSG):
        e = at(mid, t); y = 356 + i * 31
        fresh = e and t - e[0] < 0.25
        c.text(38, y, nm, 15, FG if e else DIM, True); c.text(166, y + 1, f"0x{mid:03X}", 13, DIM, False, True)
        c.text(214, y + 1, fn(e[3]) if e else "not sent yet", 13, (AMBER if fresh else FG) if e else DIM, False, True)
    c.log(536, 322, 720, 360, log, t, sz=14)
    c.footer(VER, SPEED)

SPEED = 10 / 15
n = render(draw, 10.0, SPEED, "sim/screenshots/car.gif")
print("frames", n)
