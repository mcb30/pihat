"""Pi Hat EEPROM exceptions"""

__all__ = [
    'EepromValueError',
    'EepromSignatureError',
    'EepromCrcError',
    'EepromLengthError',
]


class EepromValueError(ValueError):
    """EEPROM value error"""


class EepromSignatureError(EepromValueError):
    """EEPROM magic signature error"""


class EepromCrcError(EepromValueError):
    """EEPROM CRC error"""


class EepromLengthError(EepromValueError):
    """EEPROM length error"""
