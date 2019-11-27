"""Device tests"""

from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import UUID
import sys
from pihat.eeprom import *


class DeviceTest(unittest.TestCase):
    """Device tests"""

    @classmethod
    def setUpClass(cls):
        """Initialise test suite"""
        module = sys.modules[cls.__module__]
        cls.files = Path(module.__file__).parent / 'files'

    def test_load(self):
        """Test loading EEPROM from dummy device"""
        with patch.object(EepromDevice, 'sysfs_eeprom',
                          self.files / 'sample.eep'):
            with patch.object(EepromDevice, 'dtoverlay') as dtoverlay:
                eeprom = EepromDevice.load()
                dtoverlay.assert_not_called()
            self.assertEqual(eeprom.uuid,
                             UUID('23872014-7f74-46f9-b521-02456d9c8261'))

    def test_autocreate(self):
        """Test triggering autocreate"""
        with patch.object(EepromDevice, 'sysfs_eeprom',
                          self.files / '__nonexistent_file__'):
            with patch.object(EepromDevice, 'dtoverlay') as dtoverlay:
                with self.assertRaises(FileNotFoundError):
                    EepromDevice.load()
                dtoverlay.assert_called_once()
            with patch.object(EepromDevice, 'dtoverlay') as dtoverlay:
                with self.assertRaises(FileNotFoundError):
                    with EepromDevice.open() as eeprom:
                        pass
                dtoverlay.assert_called_once()

    def test_no_autocreate(self):
        """Test disabling autocreate"""
        with patch.object(EepromDevice, 'sysfs_eeprom',
                          self.files / '__nonexistent_file__'):
            with patch.object(EepromDevice, 'dtoverlay') as dtoverlay:
                with self.assertRaises(FileNotFoundError):
                    EepromDevice.load(autocreate=False)
                dtoverlay.assert_not_called()
            with patch.object(EepromDevice, 'dtoverlay') as dtoverlay:
                with self.assertRaises(FileNotFoundError):
                    with EepromDevice.open(autocreate=False) as eeprom:
                        pass
                dtoverlay.assert_not_called()

    def test_dtoverlay(self):
        """Test device tree overlay"""
        with patch.object(EepromDevice, 'sysfs_eeprom',
                          self.files / 'sample.eep'):
            with patch.object(EepromDevice, 'sysfs_overlay') as sysfs_overlay:
                self.assertTrue(EepromDevice.dtoverlay())
                sysfs_overlay.mkdir.assert_called_once()
        with patch.object(EepromDevice, 'sysfs_eeprom',
                          self.files / '__nonexistent_file__'):
            with patch.object(EepromDevice, 'sysfs_overlay') as sysfs_overlay:
                self.assertFalse(EepromDevice.dtoverlay())
                sysfs_overlay.mkdir.assert_called_once()
