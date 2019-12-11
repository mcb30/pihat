"""Description file tests"""

import json
import unittest
from uuid import UUID
from yaml import safe_load, safe_dump
from pihat.eeprom import (Eeprom, EepromDescription, EepromGpioDrive,
                          EepromGpioSlew, EepromGpioHysteresis,
                          EepromGpioBackPower, EepromGpioFunction,
                          EepromGpioPull)


class DescriptionTest(unittest.TestCase):
    """Description file tests"""

    def test_encode(self):
        """Test encoding"""
        data = {
            'uuid': UUID('3c24999a-74fd-4d83-ae8a-66cf941562e9'),
            'vstr': b'Factory',
            'drive': EepromGpioDrive.MA_4,
        }
        expected = {
            'uuid': '3c24999a-74fd-4d83-ae8a-66cf941562e9',
            'vstr': 'Factory',
            'drive': '4 mA',
        }
        desc = EepromDescription(data)
        self.assertEqual(desc.encoded, expected)
        self.assertEqual(json.loads(desc.json), expected)
        self.assertEqual(safe_load(desc.yaml), expected)

    def test_decode(self):
        """Test decoding"""
        encoded = {
            'uuid': '8a1ca5dc-40c8-409a-86de-cb457ac3fed8',
            'hysteresis': 'enabled',
            'drive': '8 mA',
            'back_power': '2000 mA',
            'slew': 2,
            'pins': {
                '3': {'function': 'output'},
                '4': {'function': 'alt4', 'pull': 'up'},
            },
        }
        expected = {
            'uuid': UUID('8a1ca5dc-40c8-409a-86de-cb457ac3fed8'),
            'hysteresis': EepromGpioHysteresis.ENABLED,
            'drive': EepromGpioDrive.MA_8,
            'back_power': EepromGpioBackPower.MA_2000,
            'slew': EepromGpioSlew.UNLIMITED,
            'pins': {
                3: {
                    'function': EepromGpioFunction.OUTPUT,
                },
                4: {
                    'function': EepromGpioFunction.ALT4,
                    'pull': EepromGpioPull.UP,
                },
            },
        }
        desc = EepromDescription(encoded=encoded)
        self.assertEqual(desc.data, expected)
        json_desc = EepromDescription(json=json.dumps(encoded))
        self.assertEqual(json_desc.data, expected)
        yaml_desc = EepromDescription(yaml=safe_dump(encoded))
        self.assertEqual(yaml_desc.data, expected)

    def test_apply(self):
        """Test applying description to EEPROM"""
        eeprom = Eeprom()
        desc = EepromDescription(encoded={
            'uuid': 'b98d4f05-9749-44a8-b821-5efbe0c7a215',
            'pid': 0x8086,
            'pver': 0x00b0,
            'vstr': 'The Maker',
            'pstr': 'The Thing',
            'drive': '4 mA',
            'slew': 1,
            'hysteresis': 'enabled',
            'back_power': '1300 mA',
            'pins': {
                '18': {'function': 'alt2'},
                '19': {'pull': 'up'},
            },
        })
        desc.apply(eeprom)
        self.assertEqual(eeprom.uuid,
                         UUID('b98d4f05-9749-44a8-b821-5efbe0c7a215'))
        self.assertEqual(eeprom.pid, 0x8086)
        self.assertEqual(eeprom.pver, 0x00b0)
        self.assertEqual(eeprom.vstr, b'The Maker')
        self.assertEqual(eeprom.pstr, b'The Thing')
        self.assertEqual(eeprom.bank.drive, EepromGpioDrive.MA_4)
        self.assertEqual(eeprom.bank.slew, EepromGpioSlew.LIMITED)
        self.assertEqual(eeprom.bank.hysteresis, EepromGpioHysteresis.ENABLED)
        self.assertEqual(eeprom.power.back_power, EepromGpioBackPower.MA_1300)
        self.assertTrue(eeprom.pins[18].used)
        self.assertEqual(eeprom.pins[18].function, EepromGpioFunction.ALT2)
        self.assertTrue(eeprom.pins[19].used)
        self.assertEqual(eeprom.pins[19].pull, EepromGpioPull.UP)

    def test_describe(self):
        """Test describing EEPROM"""
        eeprom = Eeprom()
        eeprom.uuid = UUID('691478b9-7f84-4c56-9063-bdda96804aad')
        eeprom.vstr = b'Vendor'
        eeprom.pstr = b'Product'
        eeprom.pins[5].used = True
        eeprom.pins[5].pull = EepromGpioPull.UP
        eeprom.pins[7].used = True
        eeprom.pins[7].function = EepromGpioFunction.ALT5
        desc = EepromDescription.from_eeprom(eeprom)
        self.assertEqual(desc.encoded, {
            'uuid': '691478b9-7f84-4c56-9063-bdda96804aad',
            'vstr': 'Vendor',
            'pstr': 'Product',
            'pins': {
                5: {'function': 'input', 'pull': 'up'},
                7: {'function': 'alt5'},
            },
        })
