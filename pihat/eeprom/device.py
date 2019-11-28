"""EEPROM device"""

from pathlib import Path
import pkg_resources
import time
from .file import EepromFile

__all__ = [
    'EepromDevice',
]


class EepromDevice(EepromFile):
    """EEPROM stored in an i2c EEPROM device"""

    dtbo = pkg_resources.resource_string(__name__, 'ideeprom.dtbo')

    sysfs_eeprom = Path('/sys/class/i2c-adapter/i2c-99/99-0050/eeprom')
    sysfs_overlay = Path('/sys/kernel/config/device-tree/overlays/ideeprom')

    eeprom_wait_interval = 0.1
    eeprom_wait_max = 2.0

    @classmethod
    def dtoverlay(cls):
        """Create EEPROM device via devicetree overlay"""
        cls.sysfs_overlay.mkdir(exist_ok=True)
        dtbofile = cls.sysfs_overlay / 'dtbo'
        with dtbofile.open('wb') as f:
            f.write(cls.dtbo)
        expired = time.time() + cls.eeprom_wait_max
        while time.time() < expired:
            if cls.sysfs_eeprom.exists():
                return True
            time.sleep(cls.eeprom_wait_interval)
        return False

    @classmethod
    def device(cls, autocreate=True):
        """Get EEPROM device name"""
        if autocreate and not cls.sysfs_eeprom.exists():
            cls.dtoverlay()
        return cls.sysfs_eeprom

    @classmethod
    def open(cls, autocreate=True, **kwargs):
        filename = cls.device(autocreate=autocreate)
        return super().open(filename=filename, **kwargs)

    @classmethod
    def load(cls, file=None, autocreate=True, **kwargs):
        if file is None:
            file = cls.device(autocreate=autocreate)
        return super().load(file=file, **kwargs)
