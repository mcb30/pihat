# Build test EEPROM files using the offical Raspberry Pi tools from
# https://github.com/raspberrypi/hats.git

EEPMAKE		:= eepmake

TXTFILES	:= $(wildcard *.txt)
EEPFILES	:= $(patsubst %.txt,%.eep,$(TXTFILES))

all : $(EEPFILES)

clean :
	$(RM) $(EEPFILES)

%.eep : %.txt
	$(EEPMAKE) $< $@
