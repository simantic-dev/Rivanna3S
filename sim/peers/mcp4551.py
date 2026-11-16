# Microchip MCP4551 (MCP45X1 family, 8-bit, 257 taps, volatile) I2C digital pot.
# Source: Microchip DS22096B (MCP453X/455X/463X/465X).
#   - 7-bit address '0101 11' + A0, so 0x2E or 0x2F (section 6.2).
#   - Command byte: AD3:AD0 (bits 7:4), C1:C0 (bits 3:2: 00 write, 01 increment,
#     10 decrement, 11 read), D9:D8 (bits 1:0) (section 7.1). Write is followed
#     by one data byte D7:D0. Data memory is 9 bits wide, D9 is ignored.
#   - Memory map (table 7-2): 00h volatile wiper 0 (POR mid-scale 080h),
#     04h TCON (POR 1FFh), 05h reserved, reads 1F7h (section 4.2.1.1). Increment
#     and decrement are valid on 00h only, and saturate at 000h / 100h.
#   - An invalid address/command combination is not acknowledged, and the
#     rest of the transfer is ignored (section 7.3).
# A read returns 2 bytes: the register's bits 15:8 then 7:0.
WIPER, TCON, STATUS = 0x0, 0x4, 0x5
WRITE, INC, DEC, READ = 0, 1, 2, 3


class Slave:
    # The controller may hand one write over in several on_write chunks (the
    # STM32 v2 I2C delivers per NBYTES/RELOAD chunk), so a command byte whose
    # data byte has not arrived yet is held until the next chunk or START.
    def __init__(self, ctx):
        self.ctx = ctx
        self.regs = {WIPER: 0x080, TCON: 0x1FF, STATUS: 0x1F7}
        self.pointer = WIPER
        self.cmd = None   # write command waiting for its data byte

    def on_address(self, addr, is_read):
        self.cmd = None
        return True

    def on_write(self, data):
        for i, byte in enumerate(data):
            if self.cmd is not None:
                addr = self.cmd >> 4
                self.regs[addr] = ((self.cmd & 1) << 8) | byte
                self.ctx.info(f"mcp4551 {'wiper' if addr == WIPER else 'tcon'}=0x{self.regs[addr]:03X}")
                self.cmd = None
                continue
            addr, op = byte >> 4, (byte >> 2) & 3
            if op == WRITE and addr in (WIPER, TCON):
                self.cmd = byte
            elif op in (INC, DEC) and addr == WIPER:
                w = self.regs[WIPER] + (1 if op == INC else -1)
                self.regs[WIPER] = min(max(w, 0), 0x100)
            elif op == READ and addr in self.regs:
                self.pointer = addr
            else:
                self.ctx.warning(f"mcp4551 NACK command 0x{byte:02X}")
                return i  # ACK the bytes before the invalid command only
        return len(data)

    def on_read(self, count):
        v = self.regs[self.pointer]
        return bytes([v >> 8, v & 0xFF] * count)[:count]
