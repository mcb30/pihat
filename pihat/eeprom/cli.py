"""Pi Hat command line interface"""

import argparse
from dataclasses import dataclass, InitVar
from fdt import parse_dts, parse_dtb
from .device import EepromDevice
from .file import EepromFile

__all__ = [
    'Command',
]


@dataclass
class Command:
    """Extract/merge/replace Pi Hat ID EEPROM"""

    args: InitVar[argparse.Namespace]

    def __post_init__(self, args=None):
        self.args = self.parser().parse_args(args)

    def parser(self):
        """Argument parser"""
        parser = argparse.ArgumentParser(description=self.__doc__)
        filedev = parser.add_mutually_exclusive_group()
        filedev.add_argument('-f', '--file', help="EEPROM file")
        filedev.add_argument('-b', '--bus', type=int, help="I2C bus number")
        action = parser.add_mutually_exclusive_group()
        action.add_argument('-d', '--dump', default=self.dump, dest='action',
                            action='store_const', const=self.dump,
                            help="Dump existing EEPROM contents to stdout")
        action.add_argument('-e', '--extract', dest='action',
                            action='store_const', const=self.extract,
                            help="Extract existing EEPROM content")
        action.add_argument('-m', '--merge', dest='action',
                            action='store_const', const=self.merge,
                            help="Merge with existing EEPROM content")
        action.add_argument('-r', '--replace', dest='action',
                            action='store_const', const=self.replace,
                            help="Replace existing EEPROM content")
        dt = parser.add_mutually_exclusive_group()
        dt.add_argument('--dts', help="Devicetree source file")
        dt.add_argument('--dtb', help="Devicetree binary file")
        return parser

    def eeprom(self, **kwargs):
        """Construct EEPROM object"""
        return (
            EepromFile(self.args.file, **kwargs) if self.args.file else
            EepromDevice(bus=self.args.bus, **kwargs) if self.args.bus else
            EepromDevice(**kwargs)
        )

    def read_fdt(self):
        """Read devicetree"""
        if self.args.dts:
            with open(self.args.dts, 'r') as f:
                return parse_dts(f.read())
        else:
            with open(self.args.dtb, 'rb') as f:
                return parse_dtb(f.read())

    def write_fdt(self, fdt):
        """Write devicetree"""
        if self.args.dts:
            with open(self.args.dts, 'w') as f:
                f.write(fdt.to_dts())
        else:
            with open(self.args.dtb, 'wb') as f:
                f.write(fdt.to_dtb())

    def dump(self):
        """Dump existing EEPROM contents to stdout"""
        with self.eeprom() as eeprom:
            print(eeprom.fdt.to_dts())

    def extract(self):
        """Extract existing EEPROM content"""
        with self.eeprom() as eeprom:
            if self.args.dts or self.args.dtb:
                self.write_fdt(eeprom.fdt)

    def merge(self):
        """Merge with existing EEPROM content"""
        with self.eeprom(autosave=True) as eeprom:
            if self.args.dts or self.args.dtb:
                eeprom.fdt.merge(self.read_fdt())

    def replace(self):
        """Replace existing EEPROM content"""
        with self.eeprom(autoload=False, autosave=True) as eeprom:
            if self.args.dts or self.args.dtb:
                eeprom.fdt = self.read_fdt()

    def execute(self):
        """Execute command"""
        self.args.action()


def main(args=None):
    """Command line entry point"""
    cmd = Command(args)
    cmd.execute()


if __name__ == '__main__':
    main()
