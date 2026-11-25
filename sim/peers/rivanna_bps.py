# Rivanna3S battery protection system (BMS) on the main CAN bus. Frames and
# layouts are the team's own interface definition, Rivanna3S
# Common/can_structs/Inc/bps.h (cantools output of their BPS DBC), 11-bit IDs:
#   BpsStatus 0x406, 6 bytes, big-endian: pack_voltage u16 (0.1 V), pack_current
#     i16 (0.1 A), pack_soc u8 (0.5 %), byte5 bit0 discharge_relay_status,
#     bit1 charge_relay_status, bit2 charger_safety, bit3 charge_power_signal,
#     bit4 balancing_active.
#   BpsError 0x3AA, 4 bytes: byte0/byte1 fault bits (byte0 bit0
#     internal_cell_communication_fault ... byte1 bit7 internal_logic_fault),
#     byte3 reduced-power bits.
# RelayBoard's precharge FSM leaves WaitForEnable only once BpsStatus reports a
# non-zero pack voltage, and opens every contactor on any BpsError fault bit.
#
# MODELED SIMPLIFICATION: the DBC carries no cycle time, so STATUS_PERIOD_US is
# a stand-in for the rate set in the BMS's own configuration. FAULT_AT_TICK is
# an optional stimulus (a weak-cell fault after that many status frames);
# None turns it off.
import struct

STATUS_ID, ERROR_ID = 0x406, 0x3AA
STATUS_PERIOD_US = 100_000
PACK_VOLTAGE_DV = 1000          # 100.0 V
PACK_CURRENT_DA = 0
PACK_SOC_HALF_PCT = 160         # 80 %
DISCHARGE_RELAY_CLOSED = 0x01
FAULT_AT_TICK = None            # healthy pack all run; 80 = weak-cell fault at 8 s (STATUS_PERIOD_US)
WEAK_CELL_FAULT = 0x02          # BpsError byte0 bit1


def bps_status(pack_dv, current_da, soc_half_pct, flags):
    return struct.pack(">HhBB", pack_dv, current_da, soc_half_pct, flags)


class Node:
    def __init__(self, ctx):
        self.ctx = ctx
        self.tick = 0
        ctx.schedule_periodic(STATUS_PERIOD_US)

    def on_timer(self):
        self.tick += 1
        self.ctx.send(STATUS_ID, bps_status(PACK_VOLTAGE_DV, PACK_CURRENT_DA,
                                            PACK_SOC_HALF_PCT, DISCHARGE_RELAY_CLOSED))
        if self.tick == FAULT_AT_TICK:
            self.ctx.info("bps: BpsError weak_cell_fault")
            self.ctx.send(ERROR_ID, bytes([WEAK_CELL_FAULT, 0, 0, 0]))

    def on_frame(self, frame):
        pass
