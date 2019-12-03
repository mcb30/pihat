#!/usr/bin/env python3

"""Setup script"""

from setuptools import setup, find_packages

setup(
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: "
        "GNU General Public License v2 or later (GPLv2+)",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Boot",
        "Topic :: System :: Hardware :: Hardware Drivers",
    ],
    packages=find_packages(),
    package_data={
        'pihat': ['eeprom/eeprom.dtbo'],
    },
    install_requires=[
        'fdt',
        'setuptools',
    ],
    entry_points={
        'console_scripts': [
            'pihat-eeprom=pihat.eeprom.cli:main',
        ],
    },
)
