"""CRC-16 algorithm"""

import array
from itertools import repeat

__all__ = ['crc16']

CRC16 = 0xa001


def crctab(poly):
    """Generate CRC lookup table"""
    table = array.array('H', repeat(0, 0x100))
    crc = 0x0001
    i = 0x80
    while i:
        crc = (crc >> 1) ^ (poly if crc & 1 else 0)
        for j in range(0, 0x100, 2 * i):
            table[i ^ j] = crc ^ table[j]
        i >>= 1
    return table


def crc16(data, crc=0, table=crctab(CRC16)):
    """Calculate CRC-16"""
    for x in data:
        crc = (crc >> 8) ^ table[(x ^ crc) & 0xff]
    return crc
