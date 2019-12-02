"""Device tests"""

from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from uuid import UUID
from tempfile import NamedTemporaryFile, TemporaryDirectory
from pihat.eeprom import EepromDeviceOverlay, EepromDevice
from .test_file import FileTestBase


class OverlayTest(FileTestBase):
    """Devicetree overlay tests"""

    def test_paths(self):
        """Test constructed paths"""
        overlay = EepromDeviceOverlay(bus=42)
        self.assertEqual(
            str(overlay.directory),
            '/sys/kernel/config/device-tree/overlays/ideeprom42'
        )
        self.assertEqual(
            str(overlay.dtbo),
            '/sys/kernel/config/device-tree/overlays/ideeprom42/dtbo'
        )
        self.assertEqual(
            str(overlay.eeprom),
            '/sys/class/i2c-adapter/i2c-42/42-0050/eeprom'
        )

    def test_install(self):
        """Test device installation"""
        dtbo = BytesIO(b'hello world')
        with TemporaryDirectory() as tempdir:
            ovdir = Path(tempdir) / 'overlay'
            with patch.object(EepromDeviceOverlay, 'directory', ovdir):
                with patch.object(EepromDeviceOverlay, 'eeprom',
                                  self.files / '__nonexistent_file__'):
                    with patch.object(EepromDeviceOverlay, 'data',
                                      dtbo.getvalue()):
                        with EepromDeviceOverlay(autoremove=True):
                            dtbofile = ovdir / 'dtbo'
                            self.assertFilesEqual(dtbofile, dtbo)
                            dtbofile.unlink()
                        self.assertFalse(ovdir.exists())
                        with EepromDeviceOverlay():
                            dtbofile = ovdir / 'dtbo'
                            self.assertFilesEqual(dtbofile, dtbo)
                        self.assertTrue(ovdir.exists())


class DeviceTest(FileTestBase):
    """Device tests"""

    def test_load(self):
        """Test loading EEPROM from dummy device"""
        eeprom = EepromDevice()
        with patch.object(EepromDeviceOverlay, 'eeprom',
                          self.files / 'sample.eep'):
            with patch.object(eeprom.overlay, 'install') as install:
                eeprom.load()
                install.assert_not_called()
            self.assertEqual(eeprom.uuid,
                             UUID('23872014-7f74-46f9-b521-02456d9c8261'))

    def test_autocreate(self):
        """Test triggering autocreate"""
        eeprom = EepromDevice()
        with patch.object(EepromDeviceOverlay, 'eeprom',
                          self.files / '__nonexistent_file__'):
            with patch.object(eeprom.overlay, 'install') as install:
                with self.assertRaises(FileNotFoundError):
                    eeprom.load()
                install.assert_called_once()
            with patch.object(eeprom.overlay, 'install') as install:
                with self.assertRaises(FileNotFoundError):
                    with eeprom:
                        pass
                install.assert_called_once()

    def test_no_autocreate(self):
        """Test disabling autocreate"""
        eeprom = EepromDevice(overlay=EepromDeviceOverlay(autocreate=False))
        with patch.object(EepromDeviceOverlay, 'eeprom',
                          self.files / '__nonexistent_file__'):
            with patch.object(eeprom.overlay, 'install') as install:
                with self.assertRaises(FileNotFoundError):
                    eeprom.load()
                install.assert_not_called()
            with patch.object(eeprom.overlay, 'install') as install:
                with self.assertRaises(FileNotFoundError):
                    with eeprom:
                        pass
                install.assert_not_called()

    def test_file_to_device(self):
        """Test loading from file and writing to device"""
        eeprom = EepromDevice()
        with NamedTemporaryFile() as temp:
            with patch.object(EepromDeviceOverlay, 'eeprom', Path(temp.name)):
                eeprom.load(self.files / 'sample.eep')
                eeprom.save()
            self.assertFilesEqual(temp.name, self.files / 'sample.eep')

    def test_device_to_file(self):
        """Test loading from device and saving to file"""
        eeprom = EepromDevice()
        with NamedTemporaryFile() as temp:
            with patch.object(EepromDeviceOverlay, 'eeprom',
                              self.files / 'spidev.eep'):
                eeprom.load()
                eeprom.save(temp.name)
            self.assertFilesEqual(temp.name, self.files / 'spidev.eep')

    def test_bus(self):
        """Test specifying I2C bus"""
        eeprom = EepromDevice(bus=1)
        self.assertEqual(eeprom.overlay.bus, 1)
