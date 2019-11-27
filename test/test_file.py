"""File tests"""

from contextlib import nullcontext
from io import IOBase
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile, TemporaryFile
import unittest
from uuid import UUID
from pihat.eeprom import *


class FileTest(unittest.TestCase):
    """File tests"""

    @classmethod
    def setUpClass(cls):
        """Initialise test suite"""
        module = sys.modules[cls.__module__]
        cls.files = Path(module.__file__).parent / 'files'

    def assertFilesEqual(self, file1, file2):
        """Assert that files have identical content"""
        def filecontext(file):
            if isinstance(file, IOBase):
                file.seek(0)
                return nullcontext(file)
            return open(file, 'rb')
        with filecontext(file1) as fh1, filecontext(file2) as fh2:
            self.assertEqual(fh1.read(), fh2.read())

    def test_load_name(self):
        """Test loading EEPROM by filename"""
        eeprom = EepromFile.load(self.files / 'sample.eep')
        self.assertEqual(eeprom.uuid,
                         UUID('23872014-7f74-46f9-b521-02456d9c8261'))
        self.assertEqual(eeprom.pid, 0xcafe)
        self.assertEqual(eeprom.pver, 0x0007)
        self.assertEqual(eeprom.vstr, b'The Factory')
        self.assertEqual(eeprom.pstr, b'Sample Board')
        self.assertEqual(eeprom.bank.drive, EepromGpioDrive.MA_14)
        self.assertEqual(eeprom.bank.slew, EepromGpioSlew.LIMITED)
        self.assertEqual(eeprom.bank.hysteresis, EepromGpioHysteresis.DEFAULT)
        self.assertEqual(eeprom.power.back_power, EepromGpioBackPower.MA_2000)
        self.assertFalse(eeprom.pins[1].used)
        self.assertTrue(eeprom.pins[2].used)
        self.assertEqual(eeprom.pins[2].function, EepromGpioFunction.INPUT)
        self.assertEqual(eeprom.pins[2].pull, EepromGpioPull.DEFAULT)
        self.assertEqual(eeprom.pins[3].pull, EepromGpioPull.DOWN)
        self.assertEqual(eeprom.pins[8].function, EepromGpioFunction.ALT3)

    def test_load_fh(self):
        """Test loading EEPROM from open filehandle"""
        with open(self.files / 'spidev.eep', 'rb') as f:
            eeprom = EepromFile.load(f)
        self.assertEqual(eeprom.uuid,
                         UUID('dac2b929-d621-4476-9742-1e0fa3cbc660'))
        self.assertEqual(eeprom.pstr, b'SPI Thing')
        self.assertEqual(eeprom.pins[10].function, EepromGpioFunction.ALT0)

    def test_save_name(self):
        """Test saving EEPROM by filename"""
        eeprom = EepromFile.load(self.files / 'sample.eep')
        with NamedTemporaryFile() as temp:
            eeprom.save(temp.name)
            self.assertFilesEqual(temp.name, self.files / 'sample.eep')

    def test_save_fh(self):
        """Test saving EEPROM to open filehandle"""
        eeprom = EepromFile.load(self.files / 'spidev.eep')
        with TemporaryFile() as temp:
            eeprom.save(temp)
            self.assertFilesEqual(temp, self.files / 'spidev.eep')

    def test_open(self):
        """Test opening EEPROM as context manager"""
        with EepromFile.open(self.files / 'spidev.eep') as eeprom:
            self.assertEqual(eeprom.pstr, b'SPI Thing')
            self.assertEqual(eeprom.pid, 0xfeed)

    def test_autosave(self):
        """Test automatic saving of modified EEPROM"""
        with NamedTemporaryFile() as temp:
            with open(self.files / 'sample.eep', 'rb') as original:
                temp.write(original.read())
                temp.flush()
            with EepromFile.open(temp.name, autosave=True) as eeprom1:
                self.assertEqual(eeprom1.uuid,
                                 UUID('23872014-7f74-46f9-b521-02456d9c8261'))
                self.assertEqual(eeprom1.pstr, b'Sample Board')
                eeprom1.uuid = UUID('5faf992a-2098-496c-a119-46dcb2dc0ddd')
            with EepromFile.open(temp.name, autosave=False) as eeprom2:
                self.assertEqual(eeprom2.uuid,
                                 UUID('5faf992a-2098-496c-a119-46dcb2dc0ddd'))
                self.assertEqual(eeprom2.pstr, b'Sample Board')
                eeprom2.pstr = b'Nothing'
            with EepromFile.open(temp.name, autosave=False) as eeprom3:
                self.assertEqual(eeprom3.uuid,
                                 UUID('5faf992a-2098-496c-a119-46dcb2dc0ddd'))
                self.assertEqual(eeprom3.pstr, b'Sample Board')
                eeprom3.pstr = b'Something'
                eeprom3.save()
                eeprom3.pstr = b'Else'
                eeprom3.save()
            with EepromFile.open(temp.name, autosave=False) as eeprom4:
                self.assertEqual(eeprom4.uuid,
                                 UUID('5faf992a-2098-496c-a119-46dcb2dc0ddd'))
                self.assertEqual(eeprom4.pstr, b'Else')
