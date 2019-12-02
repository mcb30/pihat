"""EEPROM device"""

from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field, InitVar
from pathlib import Path
import time
from typing import List, Optional
import pkg_resources
from .file import EepromFile

__all__ = [
    'EepromDeviceOverlay',
    'EepromDevice',
]

DEFAULT_BUS = 99


@dataclass
class EepromDeviceOverlay:
    """EEPROM devicetree overlay"""

    bus: int = DEFAULT_BUS
    autocreate: bool = True
    autoremove: bool = False
    timeout: float = 2.0
    interval: float = 0.1

    _ctx: List = field(init=False, repr=False, default_factory=list)

    @property
    def name(self):
        """Overlay name"""
        return 'ideeprom%d' % self.bus

    @property
    def data(self):
        """Overlay devicetree blob"""
        return pkg_resources.resource_string(__name__, '%s.dtbo' % self.name)

    @property
    def directory(self):
        """Overlay directory"""
        return Path('/sys/kernel/config/device-tree/overlays/%s' % self.name)

    @property
    def dtbo(self):
        """Overlay file"""
        return self.directory / 'dtbo'

    @property
    def eeprom(self):
        """EEPROM device path"""
        return Path('/sys/class/i2c-adapter/i2c-%d/%d-0050/eeprom' %
                    (self.bus, self.bus))

    def wait(self):
        """Wait for EEPROM device to exist"""
        expired = time.time() + self.timeout
        while time.time() < expired:
            if self.eeprom.exists():
                break
            time.sleep(self.interval)

    def install(self):
        """Install overlay"""
        self.directory.mkdir(exist_ok=True)
        with self.dtbo.open('wb') as fh:
            fh.write(self.data)
        self.wait()

    def remove(self):
        """Remove overlay"""
        if self.directory.exists():
            self.directory.rmdir()

    def __enter__(self):
        install = self.autocreate and not self.eeprom.exists()
        if install:
            self.install()
        self._ctx.append(install)
        return self.eeprom

    def __exit__(self, exc_type, exc_val, exc_tb):
        installed = self._ctx.pop()
        if installed and self.autoremove:
            self.remove()


@dataclass
class EepromDevice(EepromFile):
    """EEPROM stored in an i2c EEPROM device"""

    bus: InitVar[Optional[int]] = None
    overlay: EepromDeviceOverlay = field(default_factory=EepromDeviceOverlay)

    def __post_init__(self, bus):
        # pylint: disable=assigning-non-slot
        if bus is not None:
            self.overlay.bus = bus

    @contextmanager
    def open(self, file=None, mode=None):
        cm = (self.overlay if file is None and self.file is None else
              nullcontext(file))
        with cm as inner_file, super().open(inner_file, mode) as ctx:
            yield ctx
