# -*- coding: utf-8 -*-
####################### IMPORTS ########################
import spidev
import opc
from gpiozero import LED

#################### SENSOR SETUP ######################
# spi setup
spi = spidev.SpiDev()
spi.open(0, 0)
spi.mode = 1
spi.max_speed_hz = 500000

# Turn off OPC-N3
opcn3 = opc.OPCN3(spi)
opcn3.off()

# Turn off LED
led = LED(17)
led.off()
