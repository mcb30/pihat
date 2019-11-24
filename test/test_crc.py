"""CRC tests"""

from random import Random
import struct
import unittest
from pihat.eeprom.crc import crc16


class CrcTest(unittest.TestCase):
    """CRC tests"""

    def assertCrcEqual(self, data, crc):
        """Assert that CRC is equal to expected value"""
        self.assertEqual(crc16(data), crc)

    def assertCrcZero(self, data):
        """Assert that CRC is zero"""
        self.assertCrcEqual(data, 0)

    def assertCrcAppended(self, data):
        """Assert that appending CRC produces an overall CRC of zero"""
        self.assertCrcZero(data + struct.pack('<H', crc16(data)))

    def test_constants(self):
        """Test CRC of constant strings"""
        self.assertCrcEqual(b'', 0)
        self.assertCrcEqual(b'123456789', 0xbb3d)
        self.assertCrcEqual(b'Hello world!', 0x37b9)

    def test_append(self):
        """Test appending CRC to pseudo-random strings"""
        rng = Random(42)
        lengths = [rng.randint(0, 1024) for _ in range(10)]
        for length in lengths:
            data = bytes(rng.getrandbits(8) for _ in range(length))
            self.assertCrcAppended(data)
