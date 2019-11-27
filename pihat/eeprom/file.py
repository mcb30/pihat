"""EEPROM file"""

from contextlib import contextmanager, suppress
from dataclasses import dataclass
from io import BytesIO, IOBase
from typing import BinaryIO
from .layout import Eeprom

__all__ = [
    'EepromFile',
]


@dataclass
class EepromFile(Eeprom):
    """EEPROM stored in a file"""

    file: BinaryIO = BytesIO()
    autoload: bool = False
    autosave: bool = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.autosave and exc_type is None:
            self.save()
        self.close()

    @classmethod
    @contextmanager
    def open(cls, filename, mode='r+b', autoload=True, autosave=False,
             **kwargs):
        """Open EEPROM file"""
        constructor = cls.load if autoload else cls
        with open(filename, mode=mode) as file:
            with constructor(file=file, autoload=autoload,
                             autosave=autosave, **kwargs) as self:
                yield self

    def close(self):
        """Close EEPROM file"""
        self.file.close()

    @classmethod
    def load(cls, file, **kwargs):
        """Load EEPROM from file"""
        if not isinstance(file, IOBase):
            with open(file, 'rb') as fh:
                return cls.load(fh, **kwargs)
        with suppress(IOError):
            file.seek(0)
        raw = file.read()
        return cls.unpack(raw, file=file, **kwargs)

    def save(self, file=None):
        """Save EEPROM to file"""
        if file is None:
            file = self.file
        if not isinstance(file, IOBase):
            with open(file, 'wb') as fh:
                self.save(fh)
                return
        with suppress(IOError):
            file.seek(0)
            file.truncate()
        file.write(self.pack())
