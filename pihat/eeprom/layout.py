"""Pi Hat EEPROM layout"""

from abc import abstractmethod
from ctypes import (Array, LittleEndianStructure, c_uint8, c_uint16,
                    c_uint32, sizeof)
from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Optional, Type, Union
from uuid import UUID
from .constants import (EepromSignature, EepromVersion, EepromAtomType,
                        EepromGpioDrive, EepromGpioSlew, EepromGpioHysteresis,
                        EepromGpioBackPower, EepromGpioFunction,
                        EepromGpioPull)
from .crc import crc16
from .exceptions import EepromSignatureError, EepromLengthError, EepromCrcError

__all__ = [
    'EepromHeader',
    'EepromVendorInfo',
    'EepromGpioBank',
    'EepromGpioPower',
    'EepromGpioPin',
    'EepromGpioPins',
    'EepromGpioMap',
    'EepromAtom',
    'Eeprom',
]

CRC_SEED = 0
GPIO_COUNT = 28


class EepromStructure:
    """EEPROM data structure abstract base class"""

    def __bytes__(self):
        return self.pack()

    def __len__(self):
        return len(self.pack(fixup=False))

    def __eq__(self, other):
        if isinstance(self, type(other)):
            return self.pack(fixup=False) == other.pack(fixup=False)
        return NotImplemented

    def fixup(self):
        """Fix up fields for consistency"""

    def pack(self, fixup=True):
        """Pack structure to binary data"""
        if fixup:
            self.fixup()

    @classmethod
    @abstractmethod
    def unpack(cls, raw):
        """Unpack structure from binary data"""


@dataclass
class EepromTypedField:
    """A typed field within an EEPROM structure"""

    type: Type
    field: Optional[str] = None

    def __set_name__(self, owner, name):
        if self.field is None:
            self.field = '_%s' % name
        owner.register_typed_field(name)


@dataclass
class EepromEnumField(EepromTypedField):
    """An enumerated type field within an EEPROM structure"""

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.type(getattr(instance, self.field))

    def __set__(self, instance, value):
        setattr(instance, self.field, self.type(value))


@dataclass
class EepromUuidField(EepromTypedField):
    """A UUID field within an EEPROM structure"""

    type: Type = UUID

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.type(bytes=bytes(getattr(instance, self.field)))

    def __set__(self, instance, value):
        if isinstance(value, self.type):
            value = value.bytes
        ftype = type(getattr(instance, self.field))
        setattr(instance, self.field, ftype(*bytes(value)))


@dataclass
class EepromStringField(EepromTypedField):
    """A string field within an EEPROM structure"""

    type: Type = bytes
    length_field: Optional[str] = None

    def __set_name__(self, owner, name):
        super().__set_name__(owner, name)
        if self.length_field is None:
            self.length_field = '%s_len' % self.field

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.type(getattr(instance, self.field))

    def __set__(self, instance, value):
        value = self.type(value)
        setattr(instance, self.field, value)
        setattr(instance, self.length_field, len(value))


class EepromLittleEndianStructure(EepromStructure, LittleEndianStructure):
    """An EEPROM data structure"""

    _typed_fields_: List[str] = []
    """List of attribute names for typed field attributes"""

    _repr_fields_: List[str] = []
    """List of attribute names to appear in `repr` output"""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._repr_fields_ = cls._typed_fields_ + [
            f[0] for f in getattr(cls, '_fields_', ())
            if not f[0].startswith('_')
        ]

    def __init__(self, **kwargs):
        typed_kwargs = {
            k: kwargs.pop(k) for k in self._typed_fields_ if k in kwargs
        }
        super().__init__(**kwargs)
        for k, v in typed_kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, ', '.join(
            '%s=%r' % (f, getattr(self, f)) for f in self._repr_fields_
        ))

    def __len__(self):
        return sizeof(self)

    @classmethod
    def register_typed_field(cls, name):
        """Register a typed field attribute"""
        cls._typed_fields_ = cls._typed_fields_ + [name]

    def pack(self, fixup=True):
        """Pack structure to binary data"""
        super().pack(fixup=fixup)
        return bytes(memoryview(self))

    @classmethod
    def unpack(cls, raw):
        """Unpack structure from binary data"""
        try:
            return cls.from_buffer_copy(raw)
        except ValueError as exc:
            raise EepromLengthError(*exc.args)


class EepromArray(Array):
    """An EEPROM data structure array"""

    _type_: ClassVar[Type] = c_uint8
    _length_: ClassVar[int] = 0

    def __repr__(self):
        return '[%s]' % ', '.join('%r' % x for x in self)


class EepromHeader(EepromLittleEndianStructure):
    """EEPROM header"""

    _fields_ = [
        ('_signature', c_uint32),
        ('_version', c_uint8),
        ('_reserved', c_uint8),
        ('numatoms', c_uint16),
        ('eeplen', c_uint32),
    ]

    signature = EepromEnumField(EepromSignature)
    version = EepromEnumField(EepromVersion)


class EepromAtomData(EepromLittleEndianStructure):
    """EEPROM atom data"""

    type: ClassVar[EepromAtomType]

    types: ClassVar[Dict[EepromAtomType, Type]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.type is not None:
            cls.types[cls.type] = cls


class EepromVendorInfo(EepromAtomData):
    """EEPROM vendor information data"""

    type: ClassVar[EepromAtomType] = EepromAtomType.INFO

    _vstr: bytes = b''
    _pstr: bytes = b''

    _fields_ = [
        ('_uuid', c_uint8 * 16),
        ('pid', c_uint16),
        ('pver', c_uint16),
        ('_vslen', c_uint8),
        ('_pslen', c_uint8),
    ]

    uuid = EepromUuidField()
    vstr = EepromStringField(length_field='_vslen')
    pstr = EepromStringField(length_field='_pslen')

    def __len__(self):
        return sizeof(self) + len(self._vstr) + len(self._pstr)

    def fixup(self):
        super().fixup()
        self._vslen = len(self.vstr)
        self._pslen = len(self.pstr)

    def pack(self, fixup=True):
        return super().pack(fixup=fixup) + self._vstr + self._pstr

    @classmethod
    def unpack(cls, raw):
        # pylint: disable=protected-access
        self = super().unpack(raw)
        hlen = sizeof(self)
        vslen = self._vslen
        pslen = self._pslen
        if len(raw) < hlen + vslen + pslen:
            raise EepromLengthError("Underlength vendor information data")
        self._vstr = raw[hlen:(hlen + vslen)]
        self._pstr = raw[(hlen + vslen):(hlen + vslen + pslen)]
        return self


class EepromGpioBank(EepromLittleEndianStructure):
    """EEPROM GPIO bank configuration"""

    _fields_ = [
        ('_drive', c_uint8, 4),
        ('_slew', c_uint8, 2),
        ('_hysteresis', c_uint8, 2),
    ]

    drive = EepromEnumField(EepromGpioDrive)
    slew = EepromEnumField(EepromGpioSlew)
    hysteresis = EepromEnumField(EepromGpioHysteresis)


class EepromGpioPower(EepromLittleEndianStructure):
    """EEPROM GPIO powering"""

    _fields_ = [
        ('_back_power', c_uint8, 2),
        ('_reserved', c_uint8, 6),
    ]

    back_power = EepromEnumField(EepromGpioBackPower)


class EepromGpioPin(EepromLittleEndianStructure):
    """EEPROM GPIO pin description"""

    _fields_ = [
        ('_function', c_uint8, 3),
        ('_reserved', c_uint8, 2),
        ('_pull', c_uint8, 2),
        ('_used', c_uint8, 1),
    ]

    function = EepromEnumField(EepromGpioFunction)
    pull = EepromEnumField(EepromGpioPull)
    used = EepromEnumField(bool)


class EepromGpioPins(EepromArray):
    """EEPROM GPIO pin descriptions"""

    _type_ = EepromGpioPin
    _length_ = GPIO_COUNT


class EepromGpioMap(EepromAtomData):
    """EEPROM GPIO map"""

    type: ClassVar[EepromAtomType] = EepromAtomType.GPIO

    _fields_ = [
        ('bank', EepromGpioBank),
        ('power', EepromGpioPower),
        ('pins', EepromGpioPins),
    ]


class EepromAtomChecksum(EepromLittleEndianStructure):
    """EEPROM atom checksum"""

    _fields_ = [
        ("crc", c_uint16),
    ]


class EepromAtom(EepromLittleEndianStructure):
    """EEPROM atom"""

    data: Union[bytes, EepromAtomData] = b''

    _typed_fields_ = ['data']

    _fields_ = [
        ('_type', c_uint16),
        ('count', c_uint16),
        ('_dlen', c_uint32),
    ]

    type = EepromEnumField(EepromAtomType)

    def __len__(self):
        return sizeof(self) + len(self.data) + sizeof(EepromAtomChecksum)

    def fixup(self):
        # pylint: disable=attribute-defined-outside-init
        super().fixup()
        self._dlen = len(self.data) + sizeof(EepromAtomChecksum)

    def pack(self, fixup=True):
        header = super().pack(fixup=fixup)
        data = (self.data.pack(fixup=fixup) if hasattr(self.data, 'pack')
                else bytes(self.data))
        body = header + data
        checksum = EepromAtomChecksum(crc=crc16(body, CRC_SEED))
        return body + checksum

    @classmethod
    def unpack(cls, raw):
        # pylint: disable=protected-access
        self = super().unpack(raw)
        hlen = sizeof(self)
        dlen = self._dlen
        clen = sizeof(EepromAtomChecksum)
        if dlen < clen:
            raise EepromLengthError("Underlength atom CRC")
        if len(raw) < hlen + dlen:
            raise EepromLengthError("Underlength atom data")
        atom = raw[:hlen + dlen]
        if crc16(atom, CRC_SEED) != 0:
            raise EepromCrcError(
                "Invalid atom CRC 0x%04x (expected 0x%04x)" % (
                    EepromAtomChecksum.unpack(atom[-clen:]).crc,
                    crc16(atom[:-clen])
                )
            )
        self.data = atom[hlen:-clen]
        subcls = EepromAtomData.types.get(self.type)
        if subcls is not None:
            self.data = subcls.unpack(self.data)
        return self


@dataclass
class EepromAtomAttribute:
    """An EEPROM attribute located inside an atom"""

    atom: str
    attribute: Optional[str] = None

    def __set_name__(self, owner, name):
        if self.attribute is None:
            self.attribute = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        atom = getattr(instance, self.atom)
        return getattr(atom.data, self.attribute)

    def __set__(self, instance, value):
        atom = getattr(instance, self.atom)
        setattr(atom.data, self.attribute, value)


@dataclass
class EepromInfoAttribute(EepromAtomAttribute):
    """An EEPROM attribute located inside the vendor information atom"""

    atom: str = 'info'


@dataclass
class EepromGpioAttribute(EepromAtomAttribute):
    """An EEPROM attribute located inside the GPIO map atom"""

    atom: str = 'gpio'


@dataclass
class Eeprom(EepromStructure):
    """EEPROM content"""

    header: EepromHeader = field(default_factory=lambda: EepromHeader(
        signature=EepromSignature.RPI, version=EepromVersion.V1,
    ))
    atoms: List[EepromAtom] = field(default_factory=lambda: [
        EepromAtom(type=EepromAtomType.INFO, count=0, data=EepromVendorInfo()),
        EepromAtom(type=EepromAtomType.GPIO, count=1, data=EepromGpioMap()),
    ])

    uuid = EepromInfoAttribute()
    pid = EepromInfoAttribute()
    pver = EepromInfoAttribute()
    vstr = EepromInfoAttribute()
    pstr = EepromInfoAttribute()

    bank = EepromGpioAttribute()
    power = EepromGpioAttribute()
    pins = EepromGpioAttribute()

    def __len__(self):
        return len(self.header) + sum(len(x) for x in self.atoms)

    def fixup(self):
        super().fixup()
        for i, atom in enumerate(self.atoms):
            atom.count = i
            atom.fixup()
        self.header.numatoms = len(self.atoms)
        self.header.eeplen = len(self)
        self.header.fixup()

    def pack(self, fixup=True):
        super().pack(fixup=fixup)
        atoms = [x.pack(fixup=False) for x in self.atoms]
        return self.header.pack(fixup=False) + b''.join(atoms)

    @classmethod
    def unpack(cls, raw):
        header = EepromHeader.unpack(raw)
        if header.signature != EepromSignature.RPI:
            raise EepromSignatureError("Invalid EEPROM signature")
        if len(raw) < header.eeplen:
            raise EepromLengthError("Underlength EEPROM content")
        remaining = raw[len(header):header.eeplen]
        atoms = []
        while remaining:
            atom = EepromAtom.unpack(remaining)
            atoms.append(atom)
            remaining = remaining[len(atom):]
        if header.numatoms != len(atoms):
            raise EepromLengthError("Atom count mismatch")
        return cls(header, atoms)

    def atom(self, type):
        """Find first atom of a specified type"""
        # pylint: disable=redefined-builtin
        return next((x for x in self.atoms if x.type == type), None)

    @property
    def info(self):
        """Vendor information atom"""
        atom = self.atom(EepromAtomType.INFO)
        if atom is None:
            atom = EepromAtom(type=EepromAtomType.INFO,
                              data=EepromVendorInfo())
            self.atoms.insert(0, atom)
        return atom

    @property
    def gpio(self):
        """GPIO map atom"""
        atom = self.atom(EepromAtomType.GPIO)
        if atom is None:
            atom = EepromAtom(type=EepromAtomType.GPIO, data=EepromGpioMap())
            self.atoms.insert(self.atoms.index(self.info) + 1, atom)
        return atom

    @property
    def dtbo(self):
        """Device tree overlay atom"""
        atom = self.atom(EepromAtomType.DTBO)
        if atom is None:
            atom = EepromAtom(type=EepromAtomType.DTBO)
            self.atoms.insert(self.atoms.index(self.gpio) + 1, atom)
        return atom
