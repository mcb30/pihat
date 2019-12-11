"""Pi Hat EEPROM exceptions"""

__all__ = [
    'EepromValueError',
    'EepromSignatureError',
    'EepromCrcError',
    'EepromLengthError',
    'EepromVerificationError',
]


class EepromValueError(ValueError):
    """EEPROM value error"""


class EepromSignatureError(EepromValueError):
    """EEPROM magic signature error"""


class EepromCrcError(EepromValueError):
    """EEPROM CRC error"""


class EepromLengthError(EepromValueError):
    """EEPROM length error"""


class EepromVerificationError(EepromValueError):
    """EEPROM verification error"""
