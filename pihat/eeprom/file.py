"""EEPROM file"""

from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from io import IOBase
from os import PathLike
from typing import IO, List, Union
from uuid import uuid4
from .layout import Eeprom

__all__ = [
    'EepromFile',
]


@dataclass
class OpenableFile:
    """Openable file base class"""

    file: Union[None, PathLike, IO] = field(default=None, compare=False)
    mode: str = field(default='r+b', compare=False)

    _ctx: List = field(init=False, repr=False, compare=False,
                       default_factory=list)

    @contextmanager
    def open(self, file=None, mode=None):
        """Open file"""
        if file is None:
            file = self.file
        if mode is None:
            mode = self.mode
        if isinstance(file, IOBase):
            yield file
        else:
            with open(file, mode) as fh:
                yield fh

    def __enter__(self):
        # pylint: disable=no-member
        cm = self.open()
        self._ctx.append((cm, self.file))
        self.file = cm.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        (cm, self.file) = self._ctx.pop()
        return cm.__exit__(exc_type, exc_val, exc_tb)


@dataclass
class EepromFile(Eeprom, OpenableFile):
    """EEPROM stored in a file"""

    autoload: bool = field(default=True, compare=False)
    autosave: bool = field(default=False, compare=False)
    autouuid: bool = field(default=False, compare=False)

    def __enter__(self):
        super().__enter__()
        if self.autoload:
            self.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.autosave and exc_type is None:
            self.save()
        return super().__exit__(exc_type, exc_val, exc_tb)

    def pack(self, fixup=True):
        uuid = self.uuid
        try:
            if self.autouuid and not self.uuid.int:
                self.uuid = uuid4()
            return super().pack(fixup=fixup)
        finally:
            self.uuid = uuid

    def load(self, file=None, mode='rb'):
        """Load EEPROM from file"""
        with self.open(file, mode) as fh:
            with suppress(IOError):
                fh.seek(0)
            return self.unpack(fh.read())

    def save(self, file=None, mode='wb'):
        """Save EEPROM to file"""
        with self.open(file, mode) as fh:
            with suppress(IOError):
                fh.seek(0)
                fh.truncate()
            fh.write(self.pack())
