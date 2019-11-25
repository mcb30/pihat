"""Pi Hat EEPROM constants"""

from enum import IntEnum, IntFlag

__all__ = [
    'EepromSignature',
    'EepromVersion',
    'EepromAtomType',
    'EepromGpioDrive',
    'EepromGpioSlew',
    'EepromGpioHysteresis',
    'EepromGpioBackPower',
    'EepromGpioFunction',
    'EepromGpioPull',
]


class EepromSignature(IntFlag):
    """Magic signature"""

    RPI = 0x69502d52


class EepromVersion(IntFlag):
    """Structure version"""

    V1 = 1


class EepromAtomType(IntFlag):
    """Atom type"""

    INFO = 1
    GPIO = 2
    DTBO = 3
    CUSTOM = 4


class EepromGpioDrive(IntEnum):
    """GPIO bank drive"""

    DEFAULT = 0
    MA_2 = 1
    MA_4 = 2
    MA_6 = 3
    MA_8 = 4
    MA_10 = 5
    MA_12 = 6
    MA_14 = 7
    MA_16 = 8
    RESERVED_9 = 9
    RESERVED_10 = 10
    RESERVED_11 = 11
    RESERVED_12 = 12
    RESERVED_13 = 13
    RESERVED_14 = 14
    RESERVED_15 = 15


class EepromGpioSlew(IntEnum):
    """GPIO bank slew"""

    DEFAULT = 0
    LIMITED = 1
    UNLIMITED = 2
    RESERVED = 3


class EepromGpioHysteresis(IntEnum):
    """GPIO bank hysteresis"""

    DEFAULT = 0
    DISABLED = 1
    ENABLED = 2
    RESERVED = 3


class EepromGpioBackPower(IntEnum):
    """Board back powering"""

    NONE = 0
    MA_1300 = 1
    MA_2000 = 2
    RESERVED = 3


class EepromGpioFunction(IntEnum):
    """GPIO pin function"""

    INPUT = 0
    OUTPUT = 1
    ALT0 = 4
    ALT1 = 5
    ALT2 = 6
    ALT3 = 7
    ALT4 = 3
    ALT5 = 2


class EepromGpioPull(IntEnum):
    """GPIO pull direction"""

    DEFAULT = 0
    UP = 1
    DOWN = 2
    NONE = 3
