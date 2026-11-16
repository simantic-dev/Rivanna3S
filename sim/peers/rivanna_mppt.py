# Rivanna3S solar MPPT pair (MG0, MG1) on the main CAN bus. Frames and layouts
# are the team's own interface definition, Rivanna3S
# Common/can_structs/Inc/mppt.h (cantools output of their MPPT DBC), 11-bit IDs,
# little-endian:
#   MGnStatus 0x180+n, 8 bytes: input_current f32 (A), input_voltage f32 (V).
#   MGnOutputVoltageInputPower 0x280+n, 8 bytes: output_voltage f32 (V),
#     input_power f32 (W).
#   MGnPCBMOSFETTemperature 0x480+n, 4 bytes: pcb_temperature i16,
#     mosfet_temperature i16 (0.01 degC).
# No Rivanna3S board subscribes to these in this firmware; TelemetryBoard logs
# whatever it receives.
#
# MODELED SIMPLIFICATION: the DBC carries no cycle time, so PERIOD_US stands in
# for the MPPT's broadcast rate; the operating point is a fixed array state.
import struct

PERIOD_US = 1_000_000
# (input_current A, input_voltage V, output_voltage V, pcb degC, mosfet degC)
CHANNELS = [(2.5, 40.0, 100.0, 35.0, 40.0), (2.4, 39.5, 100.0, 34.0, 39.0)]


def frames(n, i_in, v_in, v_out, t_pcb, t_fet):
    return [
        (0x180 + n, struct.pack("<ff", i_in, v_in)),
        (0x280 + n, struct.pack("<ff", v_out, i_in * v_in)),
        (0x480 + n, struct.pack("<hh", round(t_pcb * 100), round(t_fet * 100))),
    ]


class Node:
    def __init__(self, ctx):
        self.ctx = ctx
        ctx.schedule_periodic(PERIOD_US)

    def on_timer(self):
        for n, ch in enumerate(CHANNELS):
            for fid, data in frames(n, *ch):
                self.ctx.send(fid, data)

    def on_frame(self, frame):
        pass
