# -*- coding: utf-8 -*-
####################### IMPORTS ########################
import spidev
import opc
import time
import datetime
from influxdb import InfluxDBClient
import mh_z19


#################### SENSOR SETUP ######################
# spi setup
spi = spidev.SpiDev()
spi.open(0, 0)
spi.mode = 1
spi.max_speed_hz = 500000

startTime = datetime.datetime.now()
startDate = datetime.date.today()
alphasense = opc.OPCN3(spi)


################### Global Variables ####################

# Set InfluxDB parameters.
host = "localhost"
port = 8086
user = "root"
password = "root"
dbname = "logger_db"
session = "test2"
now = datetime.datetime.now()
run_num = now.strftime("%Y%m%d%H%M")

# How frequently we will write sensor data from the sensor to the database (s)
sampling_period = 4


def get_data_points():
	opc_data = {}
	opc_data = alphasense.histogram()
	
	mhz19_data = mh_z19.read_all()
	
	# Get the five measurement values from the OPC sensor.
	pm1 = opc_data['PM_A']
	pm2_5 = opc_data['PM_B']
	pm10 = opc_data['PM_C']
	temperature = opc_data['Temperature']
	humidity = opc_data['Relative humidity']
	
	# Get the CO2 measurement value from the MHZ19 sensor.
	co2 = mhz19_data['co2']
	
	# Get a local timestamp
	timestamp = datetime.datetime.utcnow().isoformat()
	
	# Print out current readings to terminal
	print "****************************************"
	print "Timestamp: ", timestamp  
	print "Temperature: {0}{1}C".format(round(temperature,1), u'\u00b0'.encode('utf8'))
	print "Humidity: {0}%".format(round(humidity,1))
	print "PM  1.0: {0}{1}g/m{2}".format(round(pm1,2), u'\u00B5'.encode('utf8'), u'\u00B3'.encode('utf8'))
	print "PM  2.5: {0}{1}g/m{2}".format(round(pm2_5,2), u'\u00B5'.encode('utf8'), u'\u00B3'.encode('utf8'))
	print "PM 10.0: {0}{1}g/m{2}".format(round(pm10,2), u'\u00B5'.encode('utf8'), u'\u00B3'.encode('utf8'))
	print "C0{0}: {1}ppm".format(u"\u2082".encode('utf8'), co2)
	print "****************************************"
	
	# Create InfluxDB datapoints
	datapoints = [
			{
				"measurement": session,
				"tags": {
					"run_num": run_num
				},
				"time": timestamp,
				"fields": {
					"temperaturevalue":temperature,
					"humidityvalue":humidity,
					"pm1value":pm1,
					"pm25value":pm2_5,
					"pm10value":pm10,
					"co2value":co2
					}
				}
			]
	return datapoints
		
	

######################### RUN ###########################
# Turn the opc sensor ON
alphasense.on()
time.sleep(10)

client = InfluxDBClient(host, port, user, password, dbname)

# Read and discard the first histogram as per Alphasense guidance
data = {}
data = alphasense.histogram()
time.sleep(sampling_period)
print ""
print "***STARTED, PRESS CTRL+C TO STOP***"

# Loop for controlling the data reading. Can be aborted with ctrl + c
proceed = True
while proceed == True:
	try:
		# Write data points to InfluxDB
		datapoints = get_data_points()
		result = client.write_points(datapoints)
		if result:
			print "Data sent successfully to InfluxDB!"
		else:
			print "ERROR: data not sent successfully to InfluxDB..."
		
		# Wait for next sample
		time.sleep(sampling_period)
		
	except KeyboardInterrupt:
		proceed = False
		print ""
		print "***INTERUPT DETECTED***"
		print "***SHUTTING DOWN***"
		
		alphasense.off()
		   
# Turn the opc OFF
alphasense.off()
	
	
	
	
	
