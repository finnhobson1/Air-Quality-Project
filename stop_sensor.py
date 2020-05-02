# -*- coding: utf-8 -*-
####################### IMPORTS ########################
import spidev
import opc
import time
import datetime
from influxdb import InfluxDBClient


#################### SENSOR SETUP ######################
# spi setup
spi = spidev.SpiDev()
spi.open(0, 0)
spi.mode = 1
spi.max_speed_hz = 500000

startTime = datetime.datetime.now()
startDate = datetime.date.today()
alphasense = opc.OPCN3(spi)

alphasense.off()
