Pi HAT ID EEPROM library
========================

The Raspberry Pi `HAT specification
<https://github.com/raspberrypi/hats>`_ defines the existence of an
`ID EEPROM
<https://github.com/raspberrypi/hats/blob/master/eeprom-format.md>`_
that is connected to pins 27 and 28 of the `40-way connector
<https://pinout.xyz>`_.  This ID EEPROM contains a machine-readable
description of the HAT hardware in a form that allows the Pi to
automatically configure the GPIOs and load appropriate device drivers.

The ``pihat`` library provides a mechanism for easily extracting and
manipulating the contents of the ID EEPROM.  For example:

.. code-block:: python

   from pihat.eeprom import EepromDevice

   with EepromDevice() as eeprom:
       print("Board UUID is %s" % eeprom.uuid)
       print("Board uses %d GPIOs" %
             sum(x.used for x in eeprom.pins))

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules/pihat

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
