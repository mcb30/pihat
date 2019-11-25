"""Layout tests"""

import struct
import unittest
from uuid import UUID
from pihat.eeprom import *


class HeaderTest(unittest.TestCase):
    """Header tests"""

    def test_signature(self):
        """Test signature field behaviour"""
        rpi = struct.unpack('<L', b'R-Pi')[0]
        header = EepromHeader()
        self.assertIsInstance(header.signature, EepromSignature)
        self.assertEqual(header.signature, 0)
        header.signature = EepromSignature.RPI
        self.assertIsInstance(header.signature, EepromSignature)
        self.assertEqual(header.signature, rpi)
        header.signature = rpi
        self.assertIsInstance(header.signature, EepromSignature)
        self.assertIs(header.signature, EepromSignature.RPI)
        header.signature = 0x12345678
        self.assertIsInstance(header.signature, EepromSignature)
        self.assertEqual(header.signature, 0x12345678)

    def test_version(self):
        """Test version field behaviour"""
        header = EepromHeader()
        self.assertIsInstance(header.version, EepromVersion)
        self.assertEqual(header.version, 0)
        header.version = EepromVersion.V1
        self.assertIsInstance(header.version, EepromVersion)
        self.assertEqual(header.version, 1)
        header.version = 1
        self.assertIsInstance(header.version, EepromVersion)
        self.assertIs(header.version, EepromVersion.V1)
        header.version = 42
        self.assertIsInstance(header.version, EepromVersion)
        self.assertEqual(header.version, 42)

    def test_pack(self):
        """Test packing to binary data"""
        header = EepromHeader(
            signature=EepromSignature.RPI, version=EepromVersion.V1,
            numatoms=2, eeplen=0x204,
        )
        raw = bytes([
            0x52, 0x2d, 0x50, 0x69, 0x01, 0x00, 0x02, 0x00,
            0x04, 0x02, 0x00, 0x00
        ])
        self.assertEqual(header.pack(), raw)
        self.assertEqual(bytes(header), raw)

    def test_unpack(self):
        """Test unpacking from binary data"""
        raw = bytes([
            0x52, 0x2d, 0x50, 0x69, 0x01, 0x00, 0x03, 0x00,
            0x27, 0x08, 0x00, 0x00
        ])
        header = EepromHeader.unpack(raw)
        self.assertIsInstance(header, EepromHeader)
        self.assertEqual(header.signature, EepromSignature.RPI)
        self.assertEqual(header.version, EepromVersion.V1)
        self.assertEqual(header.numatoms, 3)
        self.assertEqual(header.eeplen, 0x827)
        self.assertEqual(header, EepromHeader(
            signature=EepromSignature.RPI, version=EepromVersion.V1,
            numatoms=3, eeplen=0x827,
        ))
        with self.assertRaises(EepromLengthError):
            EepromHeader.unpack(raw[:-1])
        self.assertEqual(EepromHeader.unpack(raw + b'padding'), header)


class VendorInfoTest(unittest.TestCase):
    """Vendor information data tests"""

    def test_uuid(self):
        """Test UUID field behaviour"""
        info = EepromVendorInfo()
        self.assertIsInstance(info.uuid, UUID)
        self.assertEqual(info.uuid, UUID(int=0))
        info.uuid = UUID('aad2525e-01c2-40ed-b624-8b5a6c810987')
        self.assertIsInstance(info.uuid, UUID)
        self.assertEqual(info.uuid,
                         UUID('aad2525e-01c2-40ed-b624-8b5a6c810987'))
        info.uuid = bytes([0x6c, 0xe6, 0x44, 0x78, 0x8b, 0xf7, 0x43, 0x51,
                           0xb2, 0xd4, 0xe9, 0x67, 0xe1, 0x78, 0x0a, 0x5f])
        self.assertIsInstance(info.uuid, UUID)
        self.assertEqual(info.uuid,
                         UUID('6ce64478-8bf7-4351-b2d4-e967e1780a5f'))

    def test_str(self):
        """Test vendor and product string field behaviour"""
        info = EepromVendorInfo()
        self.assertEqual(len(info), 22)
        info.vstr = b'hello'
        self.assertEqual(len(info), 27)
        info.pstr = b'world'
        self.assertEqual(len(info), 32)
        info.vstr = b'hello '
        self.assertEqual(len(info), 33)
        self.assertEqual(info.vstr, b'hello ')
        self.assertEqual(info.pstr, b'world')
        self.assertEqual(bytes(info), b'\0' * 20 + b'\x06\x05hello world')

    def test_pack(self):
        """Test packing to binary data"""
        info = EepromVendorInfo(
            uuid=UUID('c475c256-54e6-4470-8418-268de3f48fb8'),
            pid=0x8086, pver=0xa0, vstr=b'Vendor', pstr=b'Product',
        )
        self.assertEqual(len(info), 35)
        raw = bytes([
            0xc4, 0x75, 0xc2, 0x56, 0x54, 0xe6, 0x44, 0x70,
            0x84, 0x18, 0x26, 0x8d, 0xe3, 0xf4, 0x8f, 0xb8,
            0x86, 0x80, 0xa0, 0x00, 0x06, 0x07
        ]) + b'VendorProduct'
        self.assertEqual(info.pack(), raw)
        self.assertEqual(bytes(info), raw)

    def test_unpack(self):
        """Test unpacking from binary data"""
        raw = bytes([
            0x9b, 0x60, 0xec, 0x55, 0x8f, 0xa3, 0x4c, 0xd4,
            0x9b, 0x01, 0xa6, 0xf1, 0x7b, 0x19, 0x03, 0xb3,
            0x34, 0x12, 0xcd, 0xab, 0x07, 0x05
        ]) + b'CompanyThing'
        info = EepromVendorInfo.unpack(raw)
        self.assertEqual(info.uuid,
                         UUID('9b60ec55-8fa3-4cd4-9b01-a6f17b1903b3'))
        self.assertEqual(info.pid, 0x1234)
        self.assertEqual(info.pver, 0xabcd)
        self.assertEqual(info.vstr, b'Company')
        self.assertEqual(info.pstr, b'Thing')
        with self.assertRaises(EepromLengthError):
            EepromVendorInfo.unpack(raw[:-1])
        self.assertEqual(EepromVendorInfo.unpack(raw + b'padding'), info)


class GpioMapTest(unittest.TestCase):
    """GPIO map tests"""

    def test_bank(self):
        """Test bank field behaviour"""
        gpio = EepromGpioMap()
        self.assertIsInstance(gpio.bank.drive, EepromGpioDrive)
        self.assertEqual(gpio.bank.drive, EepromGpioDrive.DEFAULT)
        self.assertIsInstance(gpio.bank.slew, EepromGpioSlew)
        self.assertEqual(gpio.bank.slew, EepromGpioSlew.DEFAULT)
        self.assertIsInstance(gpio.bank.hysteresis, EepromGpioHysteresis)
        self.assertEqual(gpio.bank.hysteresis, EepromGpioHysteresis.DEFAULT)
        self.assertEqual(bytes(gpio.bank), b'\0')
        gpio = EepromGpioMap(
            bank=EepromGpioBank(
                drive=EepromGpioDrive.MA_12,
                slew=EepromGpioSlew.LIMITED,
                hysteresis=EepromGpioHysteresis.ENABLED,
            ),
        )
        self.assertEqual(bytes(gpio.bank), bytes([0x96]))

    def test_power(self):
        """Test power field behaviour"""
        gpio = EepromGpioMap()
        self.assertIsInstance(gpio.power.back_power, EepromGpioBackPower)
        self.assertEqual(gpio.power.back_power, EepromGpioBackPower.NONE)
        self.assertEqual(bytes(gpio.power), b'\0')
        gpio = EepromGpioMap(
            power=EepromGpioPower(back_power=EepromGpioBackPower.MA_1300)
        )
        self.assertEqual(bytes(gpio.power), bytes([0x01]))

    def test_pins(self):
        """Test pins field behaviour"""
        gpio = EepromGpioMap()
        pin = gpio.pins[7]
        self.assertIsInstance(pin.used, bool)
        self.assertFalse(pin.used)
        self.assertIsInstance(pin.function, EepromGpioFunction)
        self.assertEqual(pin.function, EepromGpioFunction.INPUT)
        self.assertIsInstance(pin.pull, EepromGpioPull)
        self.assertEqual(pin.pull, EepromGpioPull.DEFAULT)
        gpio = EepromGpioMap(
            pins=EepromGpioPins(*(
                [EepromGpioPin()] * 11 +
                [EepromGpioPin(used=True, function=EepromGpioFunction.ALT5)]
            ))
        )
        self.assertEqual(
            bytes(gpio.pins),
            b'\0\0\0\0\0\0\0\0\0\0\0\x82\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0'
        )

    def test_pack(self):
        """Test packing to binary data"""
        gpio = EepromGpioMap(
            bank=EepromGpioBank(
                drive=EepromGpioDrive.MA_4,
                hysteresis=EepromGpioHysteresis.ENABLED,
            ),
            power=EepromGpioPower(
                back_power=EepromGpioBackPower.MA_2000,
            ),
            pins=EepromGpioPins(
                EepromGpioPin(),
                EepromGpioPin(),
                EepromGpioPin(
                    used=True,
                    function=EepromGpioFunction.ALT2,
                    pull=EepromGpioPull.DOWN,
                ),
                EepromGpioPin(
                    used=True,
                    function=EepromGpioFunction.ALT4,
                ),
            ),
        )
        self.assertEqual(len(gpio), 30)
        raw = bytes([
            0x82, 0x02, 0, 0, 0xc6, 0x83, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        ])
        self.assertEqual(gpio.pack(), raw)
        self.assertEqual(bytes(gpio), raw)

    def test_unpack(self):
        """Test unpacking from binary data"""
        raw = bytes([
            0x03, 0x01, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x81,
            0, 0, 0, 0, 0xc6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xa7
        ])
        gpio = EepromGpioMap.unpack(raw)
        self.assertEqual(gpio.bank.drive, EepromGpioDrive.MA_6)
        self.assertEqual(gpio.power.back_power, EepromGpioBackPower.MA_1300)
        self.assertFalse(gpio.pins[11].used)
        self.assertTrue(gpio.pins[12].used)
        self.assertEqual(gpio.pins[12].function, EepromGpioFunction.OUTPUT)
        self.assertTrue(gpio.pins[27].used)
        self.assertEqual(gpio.pins[27].pull, EepromGpioPull.UP)
        self.assertEqual(gpio.pins[27].function, EepromGpioFunction.ALT3)
        with self.assertRaises(EepromLengthError):
            EepromGpioMap.unpack(raw[:-1])
        self.assertEqual(EepromGpioMap.unpack(raw + b'padding'), gpio)


class AtomTest(unittest.TestCase):
    """Atom tests"""

    def test_pack(self):
        """Test packing to binary data"""
        atom = EepromAtom(
            type=EepromAtomType.INFO,
            count=2,
            data=EepromVendorInfo(
                uuid=UUID('fa421d59-c8dc-483b-b773-d2112194fc60'),
                pid=0xf00d,
                vstr=b'Vendor',
            )
        )
        self.assertEqual(len(atom), 38)
        raw = bytes([
            0x01, 0x00, 0x02, 0x00, 0x1e, 0x00, 0x00, 0x00,
            0xfa, 0x42, 0x1d, 0x59, 0xc8, 0xdc, 0x48, 0x3b,
            0xb7, 0x73, 0xd2, 0x11, 0x21, 0x94, 0xfc, 0x60,
            0x0d, 0xf0, 0x00, 0x00, 0x06, 0x00, 0x56, 0x65,
            0x6e, 0x64, 0x6f, 0x72, 0x3c, 0x99
        ])
        self.assertEqual(crc16(raw), 0)
        self.assertEqual(atom.pack(), raw)
        self.assertEqual(bytes(atom), raw)

    def test_unpack(self):
        """Test unpacking from binary data"""
        raw = bytes([
            0x01, 0x00, 0x03, 0x00, 0x1a, 0x00, 0x00, 0x00,
            0x4c, 0x4b, 0xa1, 0x2f, 0xb7, 0xe5, 0x44, 0x74,
            0x8a, 0xd4, 0xd4, 0xa0, 0xe1, 0xea, 0xa2, 0x6e,
            0xce, 0xfa, 0xfe, 0xca, 0x00, 0x02, 0x49, 0x74,
            0x7a, 0x54
        ])
        atom = EepromAtom.unpack(raw)
        self.assertEqual(atom.type, EepromAtomType.INFO)
        self.assertEqual(atom.count, 3)
        self.assertIsInstance(atom.data, EepromVendorInfo)
        self.assertEqual(atom.data.uuid,
                         UUID('4c4ba12f-b7e5-4474-8ad4-d4a0e1eaa26e'))
        self.assertEqual(atom.data.pid, 0xface)
        self.assertEqual(atom.data.pver, 0xcafe)
        self.assertEqual(atom.data.vstr, b'')
        self.assertEqual(atom.data.pstr, b'It')
        with self.assertRaises(EepromLengthError):
            EepromAtom.unpack(raw[:-1])
        self.assertEqual(EepromAtom.unpack(raw + b'padding'), atom)
        with self.assertRaises(EepromCrcError):
            EepromAtom.unpack(raw[:-1] + b'\0')
        raw = bytes([
            0x2a, 0x00, 0x01, 0x00, 0x07, 0x00, 0x00, 0x00,
            0x48, 0x65, 0x6c, 0x6c, 0x6f, 0x16, 0x55
        ])
        atom = EepromAtom.unpack(raw)
        self.assertIsInstance(atom.type, EepromAtomType)
        self.assertEqual(atom.type, 42)
        self.assertEqual(atom.count, 1)
        self.assertEqual(atom.data, b'Hello')


class EepromTest(unittest.TestCase):
    """EEPROM content tests"""

    def test_proxy(self):
        """Test attribute proxying"""
        eeprom = Eeprom()
        eeprom.uuid = UUID('d97855ff-d424-43ad-9a32-4fa04d1867ad')
        eeprom.pid = 0x8086
        eeprom.pver = 0xb3
        eeprom.vstr = b'Maker'
        eeprom.pstr = b'Thing'
        eeprom.bank.drive = EepromGpioDrive.MA_8
        eeprom.power.back_power = EepromGpioBackPower.MA_2000
        eeprom.pins[4].used = True
        eeprom.pins[4].function = EepromGpioFunction.ALT3
        info = eeprom.info
        gpio = eeprom.gpio
        self.assertEqual(eeprom.atoms, [info, gpio])
        self.assertEqual(info.type, EepromAtomType.INFO)
        self.assertIsInstance(info.data, EepromVendorInfo)
        self.assertEqual(gpio.type, EepromAtomType.GPIO)
        self.assertIsInstance(gpio.data, EepromGpioMap)
        self.assertEqual(bytes(info.data), bytes([
            0xd9, 0x78, 0x55, 0xff, 0xd4, 0x24, 0x43, 0xad,
            0x9a, 0x32, 0x4f, 0xa0, 0x4d, 0x18, 0x67, 0xad,
            0x86, 0x80, 0xb3, 0x00, 0x05, 0x05
        ]) + b'MakerThing')
        self.assertEqual(bytes(gpio.data), bytes([
            0x04, 0x02, 0, 0, 0, 0, 0x87, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        ]))

    def test_autocreate(self):
        """Test automatic creation of atoms"""
        eeprom = Eeprom(atoms=[])
        self.assertEqual(eeprom.atoms, [])
        info = eeprom.info
        self.assertEqual(eeprom.atoms, [info])
        self.assertEqual(info.type, EepromAtomType.INFO)
        self.assertIsInstance(info.data, EepromVendorInfo)
        gpio = eeprom.gpio
        self.assertEqual(eeprom.atoms, [info, gpio])
        self.assertEqual(gpio.type, EepromAtomType.GPIO)
        self.assertIsInstance(gpio.data, EepromGpioMap)
        dtbo = eeprom.dtbo
        self.assertEqual(eeprom.atoms, [info, gpio, dtbo])
        self.assertEqual(dtbo.type, EepromAtomType.DTBO)
        eeprom = Eeprom(atoms=[])
        gpio = eeprom.gpio
        dtbo = eeprom.dtbo
        info = eeprom.info
        self.assertEqual(eeprom.atoms, [info, gpio, dtbo])
        eeprom.fixup()
        self.assertEqual(info.count, 0)
        self.assertEqual(gpio.count, 1)
        self.assertEqual(dtbo.count, 2)
        self.assertEqual(eeprom.header.numatoms, 3)

    def test_pack_unpack(self):
        """Test packing and unpacking of binary data"""
        eeprom = Eeprom()
        eeprom.uuid = UUID('717fa646-cf30-4529-9c5e-a17bb8cec598')
        eeprom.pstr = b'Object'
        eeprom.pins[7].used = True
        eeprom.pins[7].pull = EepromGpioPull.UP
        self.assertEqual(len(eeprom), 90)
        raw = bytes([
            0x52, 0x2d, 0x50, 0x69, 0x01, 0x00, 0x02, 0x00,
            0x5a, 0x00, 0x00, 0x00,
            0x01, 0x00, 0x00, 0x00, 0x1e, 0x00, 0x00, 0x00,
            0x71, 0x7f, 0xa6, 0x46, 0xcf, 0x30, 0x45, 0x29,
            0x9c, 0x5e, 0xa1, 0x7b, 0xb8, 0xce, 0xc5, 0x98,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x06, 0x4f, 0x62,
            0x6a, 0x65, 0x63, 0x74, 0x1a, 0x53,
            0x02, 0x00, 0x01, 0x00, 0x20, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0xa0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x55, 0xc4,
        ])
        self.assertEqual(eeprom.pack(), raw)
        self.assertEqual(bytes(eeprom), raw)
        self.assertEqual(Eeprom.unpack(raw), eeprom)
        with self.assertRaises(EepromSignatureError):
            Eeprom.unpack(b'x' + raw[1:])
        with self.assertRaises(EepromLengthError):
            Eeprom.unpack(raw[:-1])
        self.assertEqual(Eeprom.unpack(raw + b'padding'), eeprom)
        with self.assertRaises(EepromCrcError):
            Eeprom.unpack(raw[:-1] + b'\0')
