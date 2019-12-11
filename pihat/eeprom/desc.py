"""EEPROM description files"""

from dataclasses import dataclass
from json import JSONDecoder, JSONEncoder
import re
from typing import ClassVar, Dict, Type
from uuid import UUID
from schema import And, Optional, Or, Schema, Use
from yaml import safe_load, safe_dump
from .constants import (EepromGpioDrive, EepromGpioSlew, EepromGpioHysteresis,
                        EepromGpioBackPower, EepromGpioFunction,
                        EepromGpioPull)

__all__ = [
    'EepromDescription',
]


@dataclass
class EepromValue:
    """EEPROM description value"""

    type: Type

    @property
    def decoder(self):
        """Schema decoder"""
        return Use(self.type)

    @property
    def encoder(self):
        """Schema encoder"""
        return self.type


@dataclass
class EepromEnumValue(EepromValue):
    """EEPROM description enumerated value"""

    @property
    def decoder(self):
        return Or(
            And(int, Use(self.type)),
            And(str, Use(lambda x: self.type[x.upper()])),
        )

    @property
    def encoder(self):
        return And(self.type, Or(
            And(lambda x: not x.name.startswith('RESERVED_'),
                Use(lambda x: x.name.lower())),
            Use(lambda x: x.value),
        ))


@dataclass
class EepromCurrentValue(EepromValue):
    """EEPROM description enumerated electrical current value"""

    @property
    def decoder(self):
        return Or(
            And(int, Use(self.type)),
            And(str, Use(lambda x: self.type[re.sub(r'(\d+)\s*mA$', r'MA_\1',
                                                    x.upper(), flags=re.I)])),
        )

    @property
    def encoder(self):
        return And(self.type, Or(
            And(lambda x: not x.name.startswith('RESERVED_'),
                Use(lambda x: re.sub(r'ma_(\d+)$', r'\1 mA', x.name.lower()))),
            Use(lambda x: x.value),
        ))


EepromDriveValue = EepromCurrentValue(EepromGpioDrive)
EepromSlewValue = EepromEnumValue(EepromGpioSlew)
EepromHysteresisValue = EepromEnumValue(EepromGpioHysteresis)
EepromBackPowerValue = EepromCurrentValue(EepromGpioBackPower)
EepromPinFunctionValue = EepromEnumValue(EepromGpioFunction)
EepromPinPullValue = EepromEnumValue(EepromGpioPull)


@dataclass
class EepromDescription:
    """EEPROM description"""
    # pylint: disable=too-many-instance-attributes

    data: Dict

    decoder: ClassVar[Schema] = Schema({
        Optional('uuid'): And(str, Use(UUID)),
        Optional('pid'): int,
        Optional('pver'): int,
        Optional('vstr'): And(str, Use(str.encode)),
        Optional('pstr'): And(str, Use(str.encode)),
        Optional('drive'): EepromDriveValue.decoder,
        Optional('slew'): EepromSlewValue.decoder,
        Optional('hysteresis'): EepromHysteresisValue.decoder,
        Optional('back_power'): EepromBackPowerValue.decoder,
        Optional('pins'): Or({}, {
            Or(int, And(str, Use(int))): {
                Optional('function'): EepromPinFunctionValue.decoder,
                Optional('pull'): EepromPinPullValue.decoder,
            },
        }),
    })

    encoder: ClassVar[Schema] = Schema({
        Optional('uuid'): And(UUID, Use(str)),
        Optional('pid'): int,
        Optional('pver'): int,
        Optional('vstr'): And(bytes, Use(bytes.decode)),
        Optional('pstr'): And(bytes, Use(bytes.decode)),
        Optional('drive'): EepromDriveValue.encoder,
        Optional('slew'): EepromSlewValue.encoder,
        Optional('hysteresis'): EepromHysteresisValue.encoder,
        Optional('back_power'): EepromBackPowerValue.encoder,
        Optional('pins'): Or({}, {
            int: {
                Optional('function'): EepromPinFunctionValue.encoder,
                Optional('pull'): EepromPinPullValue.encoder,
            },
        }),
    })

    json_decoder: ClassVar[JSONDecoder] = JSONDecoder()
    json_encoder: ClassVar[JSONEncoder] = JSONEncoder()

    def __init__(self, data=None, encoded=None, json=None, yaml=None):
        self.data = data if data is not None else {}
        if encoded is not None:
            self.encoded = encoded
        if json is not None:
            self.json = json
        if yaml is not None:
            self.yaml = yaml

    @property
    def encoded(self):
        """Description encoded as serializable Python objects"""
        return self.encoder.validate(self.data)

    @encoded.setter
    def encoded(self, value):
        self.data = self.decoder.validate(value)

    @property
    def json(self):
        """Description encoded as JSON"""
        return self.json_encoder.encode(self.encoded)

    @json.setter
    def json(self, value):
        self.encoded = self.json_decoder.decode(value)

    @property
    def yaml(self):
        """Description encoded as YAML"""
        return safe_dump(self.encoded, sort_keys=False)

    @yaml.setter
    def yaml(self, value):
        self.encoded = safe_load(value)

    def apply(self, eeprom):
        """Apply description to EEPROM"""
        if 'uuid' in self.data:
            eeprom.uuid = self.data['uuid']
        if 'pid' in self.data:
            eeprom.pid = self.data['pid']
        if 'pver' in self.data:
            eeprom.pver = self.data['pver']
        if 'vstr' in self.data:
            eeprom.vstr = self.data['vstr']
        if 'pstr' in self.data:
            eeprom.pstr = self.data['pstr']
        if 'drive' in self.data:
            eeprom.bank.drive = self.data['drive']
        if 'slew' in self.data:
            eeprom.bank.slew = self.data['slew']
        if 'hysteresis' in self.data:
            eeprom.bank.hysteresis = self.data['hysteresis']
        if 'back_power' in self.data:
            eeprom.power.back_power = self.data['back_power']
        for i, pin in self.data.get('pins', {}).items():
            eeprom.pins[i].used = True
            if 'function' in pin:
                eeprom.pins[i].function = pin['function']
            if 'pull' in pin:
                eeprom.pins[i].pull = pin['pull']

    def describe(self, eeprom):
        """Describe EEPROM"""
        self.data = {}
        if eeprom.uuid.int:
            self.data['uuid'] = eeprom.uuid
        if eeprom.pid:
            self.data['pid'] = eeprom.pid
        if eeprom.pver:
            self.data['pver'] = eeprom.pver
        if eeprom.vstr:
            self.data['vstr'] = eeprom.vstr
        if eeprom.pstr:
            self.data['pstr'] = eeprom.pstr
        if eeprom.bank.drive:
            self.data['drive'] = eeprom.bank.drive
        if eeprom.bank.slew:
            self.data['slew'] = eeprom.bank.slew
        if eeprom.bank.hysteresis:
            self.data['hysteresis'] = eeprom.bank.hysteresis
        if eeprom.power.back_power:
            self.data['back_power'] = eeprom.power.back_power
        for i, pin in enumerate(eeprom.pins):
            if pin.used:
                self.data.setdefault('pins', {})
                self.data['pins'][i] = {'function': pin.function}
                if pin.pull:
                    self.data['pins'][i]['pull'] = pin.pull

    @classmethod
    def from_eeprom(cls, eeprom):
        """Construct description from EEPROM"""
        self = cls()
        self.describe(eeprom)
        return self
