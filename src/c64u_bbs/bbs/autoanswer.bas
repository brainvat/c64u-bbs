; =============================================================================
; C64U-BBS Auto-Answer Program
; =============================================================================
;
; This is the BASIC source for the auto-answer modem test program.
; It is tokenized into a PRG by autoanswer.py and uploaded to the C64U
; via the REST API (POST /v1/runners:run_prg).
;
; The program directly accesses the ACIA 6551 (SwiftLink) registers
; at $DE00-$DE03 to communicate over the C64U's modem emulation.
;
; ACIA Register Map (at $DE00 / 56832 decimal):
;   $DE00 (56832) - Data Register      (read: receive, write: transmit)
;   $DE01 (56833) - Status Register    (read-only)
;   $DE02 (56834) - Command Register   (write)
;   $DE03 (56835) - Control Register   (write)
;
; Status Register Bits ($DE01):
;   Bit 0 - Parity Error
;   Bit 1 - Framing Error
;   Bit 2 - Overrun
;   Bit 3 - TDRE (Transmit Data Register Empty) - 1 = ready to send
;   Bit 4 - RDRF (Receive Data Register Full) - not used on C64U
;   Bit 5 - DCD  (Data Carrier Detect)
;   Bit 6 - DSR  (Data Set Ready)
;   Bit 7 - IRQ  (Interrupt pending)
;
; Command Register Value ($DE02):
;   %00001001 = $09
;     Bit 0    = 1: DTR active (Data Terminal Ready)
;     Bit 1    = 0: IRQ from receiver disabled
;     Bit 2-3  = 10: RTS low, transmit interrupt disabled
;     Bit 4    = 0: Normal mode
;     Bit 5-7  = 000: No parity
;
; Control Register Value ($DE03):
;   %00011111 = $1F
;     Bit 0-3  = 1111: Baud rate (19200 with SwiftLink external clock)
;     Bit 4    = 1: Internal baud rate generator
;     Bit 5-6  = 00: 8 data bits
;     Bit 7    = 0: 1 stop bit
;
; How the C64U modem works:
;   - The C64U listens on a configurable TCP port (we use 6400)
;   - When a TCP client connects, the C64U's modem emulation activates
;   - The modem sends its welcome text (from /USB0/welcome.txt)
;   - The ACIA status register reflects the connection state
;   - Data written to the ACIA data register ($DE00) is sent to the TCP client
;   - Data received from TCP appears in the ACIA data register
;
; Program Flow:
;   1. Initialize ACIA registers (command + control)
;   2. Poll status register bit 3 (TDRE) for connection activity
;   3. On connection: send PETSCII welcome screen byte-by-byte
;   4. Wait 30 seconds
;   5. Hang up (reset ACIA command register)
;   6. Loop back to step 1
;
; =============================================================================

10 PRINT"{clear}":PRINT"C64U-BBS AUTO-ANSWER":PRINT
15 PRINT"WAITING FOR CONNECTION..."

; Initialize ACIA: command=$09, control=$1F
20 POKE 56834,9:POKE 56835,31

; Poll status register bit 3 (TDRE) - wait for modem activity
30 S=PEEK(56833) AND 8:IF S=0 THEN 30
35 PRINT"CONNECTION DETECTED!"

; Small delay for connection handshake
50 FORT=1TO500:NEXT

; --- PETSCII welcome screen data ---
; Each byte is a PETSCII code sent through the ACIA.
; Control codes: 147=clear screen, 13=return, 5=white, 30=green,
;   154=light blue, 158=yellow, 159=cyan
100 DATA 13,147,13,159,13,32,32,42,42,42,42,42,42,42,42
101 DATA 42,42,42,42,42,42,42,42,42,42,42,42,42,42,42
102 DATA 42,42,42,42,42,42,42,42,42,42,42,42,42,42,42
103 DATA 42,42,13,32,32,42,32,32,32,32,32,32,32,32,32
104 DATA 32,32,32,32,32,32,32,32,32,32,32,32,32,32,32
105 DATA 32,32,32,32,32,32,32,32,32,32,32,32,32,32,42
106 DATA 13,32,32,42,32,32,32,5,42,42,42,32,67,54,52
107 DATA 85,45,66,66,83,32,42,42,42,159,32,32,32,32,32
108 DATA 32,32,32,32,32,32,32,32,32,32,32,32,32,42,13
109 DATA 32,32,42,32,32,32,32,32,32,32,32,32,32,32,32
110 DATA 32,32,32,32,32,32,32,32,32,32,32,32,32,32,32
111 DATA 32,32,32,32,32,32,32,32,32,32,32,42,13,32,32
112 DATA 42,32,32,32,154,67,79,77,77,79,68,79,82,69,32
113 DATA 54,52,32,85,76,84,73,77,65,84,69,159,32,32,32
114 DATA 32,32,32,32,32,32,32,32,32,32,32,42,13,32,32
115 DATA 42,32,32,32,154,66,85,76,76,69,84,73,78,32,66
116 DATA 79,65,82,68,32,83,89,83,84,69,77,159,32,32,32
117 DATA 32,32,32,32,32,32,32,32,32,32,32,42,13,32,32
118 DATA 42,32,32,32,32,32,32,32,32,32,32,32,32,32,32
119 DATA 32,32,32,32,32,32,32,32,32,32,32,32,32,32,32
120 DATA 32,32,32,32,32,32,32,32,32,42,13,32,32,42,32
121 DATA 32,32,30,83,84,65,84,85,83,58,32,79,78,76,73
122 DATA 78,69,159,32,32,32,32,32,32,32,32,32,32,32,32
123 DATA 32,32,32,32,32,32,32,32,32,42,13,32,32,42,32
124 DATA 32,32,158,84,72,73,83,32,73,83,32,65,32,84,69
125 DATA 83,84,32,80,65,71,69,46,159,32,32,32,32,32,32
126 DATA 32,32,32,32,32,32,32,32,32,42,13,32,32,42,32
127 DATA 32,32,32,32,32,32,32,32,32,32,32,32,32,32,32
128 DATA 32,32,32,32,32,32,32,32,32,32,32,32,32,32,32
129 DATA 32,32,32,32,32,32,32,42,13,32,32,42,32,32,32
130 DATA 5,73,70,32,89,79,85,32,67,65,78,32,82,69,65
131 DATA 68,32,84,72,73,83,44,159,32,32,32,32,32,32,32
132 DATA 32,32,32,32,32,32,32,32,42,13,32,32,42,32,32
133 DATA 32,5,84,72,69,32,77,79,68,69,77,32,80,73,80
134 DATA 69,76,73,78,69,32,87,79,82,75,83,33,159,32,32
135 DATA 32,32,32,32,32,32,32,32,32,42,13,32,32,42,32
136 DATA 32,32,32,32,32,32,32,32,32,32,32,32,32,32,32
137 DATA 32,32,32,32,32,32,32,32,32,32,32,32,32,32,32
138 DATA 32,32,32,32,32,32,32,42,13,32,32,42,42,42,42
139 DATA 42,42,42,42,42,42,42,42,42,42,42,42,42,42,42
140 DATA 42,42,42,42,42,42,42,42,42,42,42,42,42,42,42
141 DATA 42,42,42,42,42,42,13,154,13,32,32,80,79,87,69
142 DATA 82,69,68,32,66,89,32,67,54,52,85,45,66,66,83
143 DATA 13,32,32,71,73,84,72,85,66,46,67,79,77,47,66
144 DATA 82,65,73,78,86,65,84,47,67,54,52,85,45,66,66
145 DATA 83,13,13,158,32,32,67,79,78,78,69,67,84,73,79
146 DATA 78,32,87,73,76,76,32,67,76,79,83,69,32,73,78
147 DATA 32,51,48,32,83,69,67,79,78,68,83,46,46,46,13
148 DATA 5,13
149 DATA -1

; --- Send loop: read DATA bytes, write to ACIA data register ---
200 RESTORE
210 READ B:IF B=-1 THEN 300
220 POKE 56832,B
230 FOR T=1 TO 20:NEXT
240 GOTO 210

; --- Post-send: wait 30 seconds then disconnect ---
300 PRINT"WELCOME SENT!"
310 FOR T=1 TO 30000:NEXT

; --- Hang up: reset ACIA, loop for next caller ---
400 POKE 56834,0
410 PRINT"DISCONNECTED."
420 PRINT"WAITING FOR NEXT CONNECTION..."
430 GOTO 20
