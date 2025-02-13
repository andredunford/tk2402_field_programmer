import numpy as np


#   Initialization constants
PROGRAM = np.array([0x50, 0x52, 0x4f, 0x47, 0x52, 0x41, 0x4d], dtype='uint8') # Hex message character "PROGRAM"
P2402 = np.array([0x50, 0x32, 0x34, 0x30, 0x32, 0x0D, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF], dtype='uint8')

#   Encryption constants
CRYPT1 = np.uint8(0x00)  # first layer XOR encryption byte (sent to radio)
CRYPT2 = np.uint8(0xbb)  # second layer XOR encryption (predetermined fixed)

#   Command constants
LISTENING = np.uint8(0x16)  # initial response from TK unit
VERSION = np.uint8(0x02)  # Version request
R = np.uint8(0x52)  # Read from transciever
W = np.uint8(0x57)  # Write from transciever
Y = np.uint8(0x59)  # Set value in transciever
P = np.uint8(0x50)  # byte 'P' to request software version
END = np.uint8(0x45)  # End byte 'E'
CONF = np.uint8(0x06)  # confirmation

#   channel structure constants
# chanEnum = np.array([0xff, 0xff], dtype='uint8')  # Channel enumeration bytes for channel numbers #1-8, and #9-16
CHAN_EMPTY = np.array([0xff] * 0x20, dtype='uint8')  # empty channel used to delete channel
CHAN_INIT = np.array(
    [0xff,  # channel number
    0xff,  # ?
    0xff, 0xff, 0xff, 0xff,  # Rx reverse order each nibble is a digit
    0xff, 0xff, 0xff, 0xff,  # Tx reverse order each nibble is a digit
    0xff,  # RX channel frequency step flag
    0xff,  # TX channel frequency step flag
    0xff, 0xff,  # QT Rx byte 1, byte 2 (lookup tables QT_b1, QT_b2)
    0xff, 0xff,  # QT Tx byte 1, byte 2 (lookup tables QT_b1, QT_b2)
    0x18,  # Optional Signalling 0x18 = None
    0xec,  # Power/Scan (HIGH nibble): 0xC(Low/Yes), 0xD (Low/No), 0xE (High/Yes), 0xF (High/No) / Channel Width (LOW nibble): 0xC(Narrow)/0xD(Wide)
    0xe6, 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x00, 0x0f, 0xff, 0xff],  # ?? optional settings
    dtype='uint8'
)

############################################################
#  QT frequency code constants, 1st byte, 2nd byte
QT_MASK = np.array([
    0.0, 067.0, 069.3, 071.9, 074.4, 077.0, 079.7, 082.5,
    085.4, 088.5, 091.5, 094.8, 097.4, 100.0, 103.5, 107.2,
    110.9, 114.8, 118.8, 123.0, 127.3, 131.8, 136.5, 141.3,
    146.2, 151.4, 156.7, 162.2, 167.9, 173.8, 179.9, 186.2,
    192.8, 203.5, 210.7, 218.1, 225.7, 233.6, 241.8, 250.3])

#############################################################
#   frequency step flag divisors
FREQ_STEPS = np.array([(2, 1250), (1, 500), (0, 750), (3, 250)])  # 0x02, 0x01, 0x00, 0x03