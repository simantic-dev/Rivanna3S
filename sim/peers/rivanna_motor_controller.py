# Rivanna3S motor controller on the main CAN bus. Frames and layouts are the
# team's own interface definition, Rivanna3S
# Common/can_structs/Inc/motor_controller.h (cantools output of their motor
# controller DBC), 11-bit IDs, little-endian bit packing. The DBC is a
# request/response controller: it sends nothing until asked.
#   MotorControllerFrameRequest 0x332, 1 byte: bit0 power_status_frame,
#     bit1 drive_status_frame, bit2 error_frame.
#   MotorControllerPowerStatus 0x325, 8 bytes: battery_voltage 10 bits,
#     battery_current 9 bits, direction 1, motor_current 10, fet_temp 5,
#     motor_rpm 12, pwm_duty 10, lead_angle 7.
#   MotorControllerDriveStatus 0x315, 5 bytes.
#   MotorControllerError 0x115, 5 bytes, all zero = no fault.
# No Rivanna3S board sends a FrameRequest in this firmware, so in the five-board
# scenario this node stays silent, as the real controller would.
REQUEST_ID, POWER_ID, DRIVE_ID, ERROR_ID = 0x332, 0x325, 0x315, 0x115
# Idle, motor stopped, battery at 100 V (battery_voltage LSB 0.5 V in their DBC).
BATTERY_VOLTAGE_RAW = 200


def power_status(battery_voltage_raw):
    v = battery_voltage_raw & 0x3FF
    return bytes([v & 0xFF, v >> 8, 0, 0, 0, 0, 0, 0])


class Node:
    def __init__(self, ctx):
        self.ctx = ctx

    def on_frame(self, frame):
        if frame["id"] != REQUEST_ID or not frame["data"]:
            return
        req = frame["data"][0]
        if req & 0x01:
            self.ctx.send(POWER_ID, power_status(BATTERY_VOLTAGE_RAW))
        if req & 0x02:
            self.ctx.send(DRIVE_ID, bytes(5))
        if req & 0x04:
            self.ctx.send(ERROR_ID, bytes(5))
