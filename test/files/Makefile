# Build test EEPROM files using the offical Raspberry Pi tools from
# https://github.com/raspberrypi/hats.git

EEPMAKE		:= eepmake
DTC		:= dtc

all : sample.eep spidev.eep

clean :
	$(RM) *.eep *.dtbo

%.dtbo : %.dts
	$(DTC) -@ $< -o $@

sample.eep : %.eep : %.txt %.dtbo
	$(EEPMAKE) $< $@ $*.dtbo

spidev.eep : %.eep : %.txt
	$(EEPMAKE) $< $@
