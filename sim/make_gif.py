"""Animates sim/out/can-frames.txt (the run's --frames capture) into sim/screenshots/car.gif.
usage: python3 sim/make_gif.py "tag"   (matplotlib, pillow)"""
import re, sys, io
from collections import defaultdict
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
pre, tx = [], defaultdict(list)
for l in open("sim/out/can-frames.txt"):
    m = re.match(r"\[(\w+)\] \[([\d.]+)s\] \(can\d\) CAN Tx id=(0x[0-9A-F]+) dlc=\d+ data=(.*)", l)
    if not m: continue
    t, i = float(m[2]), m[3]
    tx[i].append(t)
    if i == "0x258": pre.append((t, int(m[4].split()[0], 16)))
end = 10.0; frames = []
for k in range(1, 41):
    tc = end * k / 40
    fig, (a, b) = plt.subplots(2, 1, figsize=(7, 4.8), dpi=70, sharex=True, gridspec_kw={"height_ratios": [1, 1.4]})
    p = [x for x in pre if x[0] <= tc]
    a.step([t for t, _ in p], [v for _, v in p], where="post", c="C3"); a.set_ylim(-5, 260)
    a.set_ylabel("RelayBoard 0x258\nbyte 0 (hex 80 = fault)", fontsize=7)
    for i, ts in sorted(tx.items()):
        n = [t for t in ts if t <= tc]
        b.step(n, range(1, len(n) + 1), where="post", label=i)
    b.set_ylabel("CAN frames sent so far", fontsize=7); b.set_xlim(0, end); b.set_xlabel("virtual time, s")
    b.legend(fontsize=6, ncol=3, loc="upper left")
    a.set_title(f"UVA Solar Car, five G474 boards on one simulated CAN bus, t={tc:.1f} s virtual, {sys.argv[1]}", fontsize=8)
    fig.tight_layout(); bf = io.BytesIO(); fig.savefig(bf, format="png"); plt.close(fig)
    frames.append(Image.open(bf).convert("RGB").quantize(colors=64, dither=Image.Dither.NONE))
frames[0].save("sim/screenshots/car.gif", save_all=True, append_images=frames[1:], duration=[120] * 39 + [1500], loop=0, optimize=True)
