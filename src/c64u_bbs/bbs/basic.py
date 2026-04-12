"""BASIC tokenizer and PETSCII utilities for the Commodore 64.

Provides a minimal BASIC V2 tokenizer for the subset of keywords we use,
and PETSCII text encoding with control code support.
"""

from __future__ import annotations


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

# BASIC V2 token values
BASIC_TOKENS = {
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


def tokenize_basic(lines: list[str]) -> bytes:
    """Tokenize BASIC lines into a PRG file.

    This is a minimal tokenizer that handles the subset of BASIC V2
    keywords needed by the BBS tools (PRINT, POKE, PEEK, FOR, NEXT,
    GOTO, IF, THEN, READ, RESTORE, DATA, AND, LOAD, etc.).

    Returns a complete PRG file (2-byte load address at $0801 + program bytes).
    """
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
        in_data = False  # After DATA keyword, everything is literal until : or EOL

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

            # Inside DATA statements, everything is literal except :
            if in_data:
                if ch == ":":
                    in_data = False
                    # Fall through to normal tokenization for the :
                else:
                    line_bytes.append(ord(ch))
                    i += 1
                    continue

            # Try to match a token (longest match first)
            matched = False
            upper_rest = rest[i:].upper()
            for token_name, token_val in sorted(
                BASIC_TOKENS.items(), key=lambda x: -len(x[0])
            ):
                if upper_rest.startswith(token_name):
                    # For alphabetic tokens (keywords), don't match inside
                    # variable names — e.g. don't match TO inside TOTAL
                    if token_name[0].isalpha() and i > 0 and rest[i - 1].isalpha():
                        continue
                    line_bytes.append(token_val)
                    i += len(token_name)
                    matched = True
                    # Track entering DATA mode
                    if token_name == "DATA":
                        in_data = True
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
