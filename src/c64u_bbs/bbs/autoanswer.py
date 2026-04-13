"""Generate a C64 PRG that auto-answers the modem and sends a PETSCII welcome.

The generated program is a BASIC loader that directly accesses the
SwiftLink/ACIA registers at $DE00 to communicate over the modem.

ACIA 6551 registers (at $DE00 for SwiftLink):
  $DE00 - Data register (read/write)
  $DE01 - Status register (read)
  $DE02 - Command register (write)
  $DE03 - Control register (write)

Status register bits:
  Bit 3 - Transmit Data Register Empty (TDRE) - ready to send
  Bit 4 - Receive Data Register Full (RDRF) - data available (not used in 6551 on C64U)
  Bit 3 is the key one for sending

The C64U modem handles the connection lifecycle:
  - Incoming TCP connection triggers RING on the ACIA
  - The C64 program sends ATA to answer
  - After CONNECT, data flows through the ACIA data register
"""

from __future__ import annotations

from c64u_bbs.bbs.basic import text_to_petscii, tokenize_basic


# PETSCII art for the welcome screen
WELCOME_SCREEN = """
{clear}
{cyan}
  ****************************************
  *                                      *
  *   {white}*** C64U-BBS ***{cyan}                  *
  *                                      *
  *   {ltblue}Commodore 64 Ultimate{cyan}              *
  *   {ltblue}Bulletin Board System{cyan}              *
  *                                      *
  *   {green}Status: ONLINE{cyan}                     *
  *   {yellow}This is a test page.{cyan}               *
  *                                      *
  *   {white}If you can read this,{cyan}               *
  *   {white}the modem pipeline works!{cyan}           *
  *                                      *
  ****************************************
{ltblue}
  Powered by c64u-bbs
  github.com/brainvat/c64u-bbs

{yellow}  Connection will close in 30 seconds...
{white}
"""


def generate_basic_autoanswer() -> bytes:
    """Generate a BASIC program that auto-answers and sends welcome screen.

    This uses a pure BASIC approach that works with the C64U's modem:
    - Opens RS-232 channel (device 2) for SwiftLink
    - Waits for carrier detect (incoming connection)
    - Sends the welcome screen
    - Waits 30 seconds
    - Hangs up

    Returns a complete PRG file (with 2-byte load address).
    """
    # We'll generate BASIC source and tokenize it
    # For simplicity, we'll use DATA statements with the PETSCII bytes
    # and a simple send loop

    welcome_bytes = text_to_petscii(WELCOME_SCREEN)

    # Build BASIC program lines
    lines = []

    # Line 10: Print startup message
    lines.append('10 PRINT"{clear}":PRINT"C64U-BBS AUTO-ANSWER":PRINT')
    lines.append('15 PRINT"WAITING FOR CONNECTION..."')

    # Line 20: Set up SwiftLink - poke ACIA registers directly
    # Command register $DE02: %00001001 = no parity, RTS low, IRQ disabled, DTR active
    # Control register $DE03: %00011111 = 1 stop bit, 8 data bits, 19200 baud (with SwiftLink)
    lines.append("20 POKE 56834,9:POKE 56835,31")

    # Line 30-40: Wait for DCD (carrier detect) - poll status register
    # The C64U modem sets DCD when a TCP connection is established
    # Status register $DE01, bit 5 = DCD (active low in some implementations)
    # Actually, with the C64U modem, we should poll for incoming data
    lines.append("30 S=PEEK(56833) AND 8:IF S=0 THEN 30")
    lines.append('35 PRINT"CONNECTION DETECTED!"')

    # Line 50: Small delay for connection setup
    lines.append("50 FORT=1TO500:NEXT")

    # Line 100+: Send welcome screen byte by byte
    # Break welcome bytes into DATA statements (max ~80 chars per line)
    data_line = 100
    chunk_size = 15
    for i in range(0, len(welcome_bytes), chunk_size):
        chunk = welcome_bytes[i : i + chunk_size]
        data_str = ",".join(str(b) for b in chunk)
        lines.append(f"{data_line} DATA {data_str}")
        data_line += 1

    # Sentinel value
    lines.append(f"{data_line} DATA -1")

    # Line 200: Read and send loop
    lines.append("200 RESTORE")
    lines.append("210 READ B:IF B=-1 THEN 300")
    lines.append("220 POKE 56832,B")  # Write to ACIA data register
    lines.append("230 FOR T=1 TO 20:NEXT")  # Small delay between chars
    lines.append("240 GOTO 210")

    # Line 300: Wait 30 seconds then hang up
    lines.append('300 PRINT"WELCOME SENT!"')
    lines.append("310 FOR T=1 TO 30000:NEXT")

    # Line 400: Hang up - reset ACIA
    lines.append("400 POKE 56834,0")
    lines.append('410 PRINT"DISCONNECTED."')
    lines.append('420 PRINT"WAITING FOR NEXT CONNECTION..."')
    lines.append("430 GOTO 20")

    return tokenize_basic(lines)
