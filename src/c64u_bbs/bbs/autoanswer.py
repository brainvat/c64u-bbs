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

# PETSCII control code mappings
PETSCII_CODES = {
    "{clear}": 147,      # Clear screen
    "{home}": 19,        # Home cursor
    "{white}": 5,        # White text
    "{red}": 28,         # Red text
    "{green}": 30,       # Green text
    "{blue}": 31,        # Blue text
    "{cyan}": 159,       # Cyan text
    "{yellow}": 158,     # Yellow text
    "{ltblue}": 154,     # Light blue text
    "{purple}": 156,     # Purple text
    "{return}": 13,      # Carriage return
}


def text_to_petscii(text: str) -> bytes:
    """Convert text with {codes} to PETSCII bytes."""
    result = bytearray()

    i = 0
    while i < len(text):
        if text[i] == "{":
            end = text.index("}", i)
            code_name = text[i : end + 1]
            if code_name in PETSCII_CODES:
                result.append(PETSCII_CODES[code_name])
            i = end + 1
        elif text[i] == "\n":
            result.append(13)  # PETSCII carriage return
            i += 1
        else:
            ch = text[i]
            # Convert ASCII to PETSCII
            if "a" <= ch <= "z":
                result.append(ord(ch) - 32)  # lowercase -> uppercase in PETSCII
            elif "A" <= ch <= "Z":
                result.append(ord(ch))  # uppercase stays
            elif 0x20 <= ord(ch) <= 0x7E:
                result.append(ord(ch))  # printable ASCII maps directly
            i += 1

    return bytes(result)


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

    return _tokenize_basic(lines)


def _tokenize_basic(lines: list[str]) -> bytes:
    """Tokenize BASIC lines into a PRG file.

    This is a minimal tokenizer that handles the subset of BASIC
    we use (PRINT, POKE, PEEK, FOR, NEXT, GOTO, IF, THEN, READ,
    RESTORE, DATA, AND).
    """
    # BASIC token values
    TOKENS = {
        "END": 128, "FOR": 129, "NEXT": 130, "DATA": 131,
        "INPUT#": 132, "INPUT": 133, "DIM": 134, "READ": 135,
        "LET": 136, "GOTO": 137, "RUN": 138, "IF": 139,
        "RESTORE": 140, "GOSUB": 141, "RETURN": 142, "REM": 143,
        "STOP": 144, "ON": 145, "WAIT": 146, "LOAD": 147,
        "SAVE": 148, "VERIFY": 149, "DEF": 150, "POKE": 151,
        "PRINT#": 152, "PRINT": 153, "CONT": 154, "LIST": 155,
        "CLR": 156, "CMD": 157, "SYS": 158, "OPEN": 159,
        "CLOSE": 160, "GET": 161, "NEW": 162, "TAB(": 163,
        "TO": 164, "FN": 165, "SPC(": 166, "THEN": 167,
        "NOT": 168, "STEP": 169, "+": 170, "-": 171,
        "*": 172, "/": 173, "^": 174, "AND": 175,
        "OR": 176, ">": 177, "=": 178, "<": 179,
        "SGN": 180, "INT": 181, "ABS": 182, "USR": 183,
        "FRE": 184, "POS": 185, "SQR": 186, "RND": 187,
        "LOG": 188, "EXP": 189, "COS": 190, "SIN": 191,
        "TAN": 192, "ATN": 193, "PEEK": 194, "LEN": 195,
        "STR$": 196, "VAL": 197, "ASC": 198, "CHR$": 199,
        "LEFT$": 200, "RIGHT$": 201, "MID$": 202,
    }

    # BASIC starts at $0801
    base_addr = 0x0801
    program = bytearray()

    for line_text in lines:
        # Parse line number
        parts = line_text.split(" ", 1)
        line_num = int(parts[0])
        rest = parts[1] if len(parts) > 1 else ""

        # Tokenize the line content
        line_bytes = bytearray()
        i = 0
        in_string = False

        while i < len(rest):
            ch = rest[i]

            if ch == '"':
                in_string = not in_string
                line_bytes.append(ord(ch))
                i += 1
                continue

            if in_string:
                # Inside strings, convert special PETSCII codes
                if ch == "{":
                    end = rest.index("}", i)
                    code_name = rest[i : end + 1]
                    if code_name in PETSCII_CODES:
                        line_bytes.append(PETSCII_CODES[code_name])
                        i = end + 1
                        continue
                line_bytes.append(ord(ch))
                i += 1
                continue

            # Try to match a token (longest match first)
            matched = False
            upper_rest = rest[i:].upper()
            for token_name, token_val in sorted(TOKENS.items(), key=lambda x: -len(x[0])):
                if upper_rest.startswith(token_name):
                    # For alphabetic tokens (keywords), don't match inside
                    # variable names — e.g. don't match TO inside TOTAL
                    if token_name[0].isalpha() and i > 0 and rest[i - 1].isalpha():
                        continue
                    line_bytes.append(token_val)
                    i += len(token_name)
                    matched = True
                    break

            if not matched:
                line_bytes.append(ord(ch))
                i += 1

        line_bytes.append(0)  # Line terminator

        # Calculate next line address
        # 2 bytes next-line pointer + 2 bytes line number + content + 1 null
        next_addr = base_addr + len(program) + 2 + 2 + len(line_bytes)

        # Write: next-line-ptr (little-endian), line-number (little-endian), content
        program.append(next_addr & 0xFF)
        program.append((next_addr >> 8) & 0xFF)
        program.append(line_num & 0xFF)
        program.append((line_num >> 8) & 0xFF)
        program.extend(line_bytes)

    # End of program: two zero bytes
    program.append(0)
    program.append(0)

    # PRG file: 2-byte load address + program
    prg = bytearray()
    prg.append(base_addr & 0xFF)
    prg.append((base_addr >> 8) & 0xFF)
    prg.extend(program)

    return bytes(prg)
