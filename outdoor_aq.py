"""
This script regularly takes air quality measurements from the Alphasense OPC-N3
and 5 different Alphasense electrochemical B4 gas sensors. 
"""

####################### IMPORTS ########################

import spidev
import opc
import time
import datetime
from ADCPi import ADCPi
from influxdb import InfluxDBClient


##################### SENSOR SETUP #####################

# Setup SPI
spi = spidev.SpiDev()
spi.open(0, 0)
spi.mode = 1
spi.max_speed_hz = 500000

# Setup OPC-N3
opcn3 = opc.OPCN3(spi)

# Setup ADCs for gas sensors
adc1 = ADCPi(0x68, 0x69, 16) 	# Channels: SO2 (1-2), NO2 (3-4), NO2+O3 (5-6), CO (7-8) 
adc2 = ADCPi(0x6A, 0x6B, 16)	# Channels: NO (1-2)


################## GLOBAL VARIABLES ####################

# Node information
node_id = 1

# Sampling period
sampling_period = 3.4 	# 5s total (loop takes approx. 1.6s) 


##################### FUNCTIONS ########################

def get_data_points():
	
	timestamp = datetime.datetime.utcnow().isoformat()
	
	print "****************************************"
	print "Timestamp: ", timestamp  
	print ""
	
	temp = 0
	humidity = 0
	
	print "Temperature: {0}{1}C".format("?", u'\u00b0'.encode('utf8'))
	print "Humidity: {0}%".format("?")
	print ""
	
	so2_w_raw = adc1.read_voltage(1) * 1000.0
	so2_a_raw = adc1.read_voltage(2) * 1000.0

	no2_w_raw = adc1.read_voltage(3) * 1000.0
	no2_a_raw = adc1.read_voltage(4) * 1000.0

	ox_w_raw = adc1.read_voltage(5) * 1000.0
	ox_a_raw = adc1.read_voltage(6) * 1000.0

	co_w_raw = adc1.read_voltage(7) * 1000.0
	co_a_raw = adc1.read_voltage(8) * 1000.0

	no_w_raw = adc2.read_voltage(1) * 1000.0
	no_a_raw = adc2.read_voltage(2) * 1000.0

	print "EC Sensor Raw Voltages:"
	print "SO2:    WE = {0}mV, AE = {1}mV".format(round(so2_w_raw,3), round(so2_a_raw,3))
	print "NO2:    WE = {0}mV, AE = {1}mV".format(round(no2_w_raw,3), round(no2_a_raw,3))
	print "NO2+O3: WE = {0}mV, AE = {1}mV".format(round(ox_w_raw,3), round(ox_a_raw,3))
	print "CO:     WE = {0}mV, AE = {1}mV".format(round(co_w_raw,3), round(co_a_raw,3))
	print "NO:     WE = {0}mV, AE = {1}mV".format(round(no_w_raw,3), round(no_a_raw,3))
	print ""
	
	pm_data = opcn3.histogram()
	pm2_5 = pm_data['PM_B']
	pm10 = pm_data['PM_C']
	
	print "PM Measurements:"
	print "PM  2.5: {0}{1}g/m{2}".format(round(pm2_5,2), u'\u00B5'.encode('utf8'), u'\u00B3'.encode('utf8'))
	print "PM 10.0: {0}{1}g/m{2}".format(round(pm10,2), u'\u00B5'.encode('utf8'), u'\u00B3'.encode('utf8'))
	print "****************************************"
	print ""
	


######################### RUN ###########################

print "***STARTING SENSORS***"

# Turn on OPC sensor
opcn3.on()
time.sleep(10)

# Read and discard the first histogram as per Alphasense guidance
data = {}
data = opcn3.histogram()
time.sleep(sampling_period)

print ""
print "***SENSORS STARTED, PRESS CTRL+C TO STOP***"
print "" 

# Loop for taking measurements from sensors, stop with CTRL+C
proceed = True
while proceed == True:
	try:
		# Take measurements from sensors
		datapoints = get_data_points()
		
		# Wait for next sample
		time.sleep(sampling_period)
		
	except KeyboardInterrupt:
		proceed = False
		print ""
		print "***INTERUPT DETECTED***"
		print "***SHUTTING DOWN***"
		
		opcn3.off()
		   
# Turn the opc OFF
opcn3.off()
