"""
This script regularly takes air quality measurements from the Alphasense OPC-N3
and 5 different Alphasense electrochemical B4 gas sensors. 
"""

####################### IMPORTS ########################

import spidev
import opc
import time
import datetime
import csv
import logging
import json
import Adafruit_DHT
from ADCPi import ADCPi
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient


##################### SENSOR SETUP #####################

# Setup SPI
spi = spidev.SpiDev()
spi.open(0, 0)
spi.mode = 1
spi.max_speed_hz = 500000

# Setup OPC-N3
opcn3 = opc.OPCN3(spi)

# Setup ADCs for gas sensors
adc1 = ADCPi(0x68, 0x69, 16) 	# Channels: SO2 (1-2), NO2 (3-4), NO2+O3 (5-6), 
adc2 = ADCPi(0x6A, 0x6B, 16)	# Channels: CO (1-2) , NO (3-4)

# Setup DHT22 temp/humidity sensor
dht22 = Adafruit_DHT.DHT22
dht_pin = 4


################## GLOBAL VARIABLES ####################

# Node information
node_id = 1

# Sampling period
sampling_period = 3.0 # 5-10s total, AWS connection time uncertain

# AWS IoT variables
endpoint = "a33igdsnv7g3xz-ats.iot.eu-west-2.amazonaws.com"
port = 8883
root_CA_path = "/home/pi/outdoor-node/certs/AmazonRootCA1.pem"
cert_path = "/home/pi/outdoor-node/certs/600feb81cb-certificate.pem.crt"
priv_key_path = "/home/pi/outdoor-node/certs/600feb81cb-private.pem.key"
thing_name = "RPi-AQ-Node1"
client_id = "RPi-AQ-Node1"


##################### FUNCTIONS ########################

def get_data():
	
	with open("/home/pi/outdoor-node/data/node" + str(node_id) + "_" + now + ".csv", 'a') as f:
		writer = csv.DictWriter(f, fieldnames=fnames)  
		csv_row = {}
		
		timestamp = datetime.datetime.utcnow().isoformat()
		csv_row['timestamp'] = timestamp
		
		print "****************************************"
		print "Timestamp: ", timestamp  
		print ""
		
		humidity, temp = Adafruit_DHT.read_retry(dht22, dht_pin)
		csv_row['temperature'] = round(temp,2)
		csv_row['humidity'] = round(humidity,2)
		
		print "Temperature: {0}{1}C".format(round(temp,1), u'\u00b0'.encode('utf8'))
		print "Humidity: {0}%".format(round(humidity,1))
		print ""
		
		so2_w_raw = adc1.read_voltage(1) * 1000.0
		so2_a_raw = adc1.read_voltage(2) * 1000.0
		csv_row['so2_we'] = round(so2_w_raw,3)
		csv_row['so2_ae'] = round(so2_a_raw,3)

		no2_w_raw = adc1.read_voltage(3) * 1000.0
		no2_a_raw = adc1.read_voltage(4) * 1000.0
		csv_row['no2_we'] = round(no2_w_raw,3)
		csv_row['no2_ae'] = round(no2_a_raw,3)

		ox_w_raw = adc1.read_voltage(5) * 1000.0
		ox_a_raw = adc1.read_voltage(6) * 1000.0
		csv_row['ox_we'] = round(ox_w_raw,3)
		csv_row['ox_ae'] = round(ox_a_raw,3)

		co_w_raw = adc1.read_voltage(1) * 1000.0
		co_a_raw = adc1.read_voltage(2) * 1000.0
		csv_row['co_we'] = round(co_w_raw,3)
		csv_row['co_ae'] = round(co_a_raw,3)

		no_w_raw = adc2.read_voltage(3) * 1000.0
		no_a_raw = adc2.read_voltage(4) * 1000.0
		csv_row['no_we'] = round(no_w_raw,3)
		csv_row['no_ae'] = round(no_a_raw,3)

		print "EC Sensor Raw Voltages:"
		print "SO2:    WE = {0}mV, AE = {1}mV".format(round(so2_w_raw,3), round(so2_a_raw,3))
		print "NO2:    WE = {0}mV, AE = {1}mV".format(round(no2_w_raw,3), round(no2_a_raw,3))
		print "NO2+O3: WE = {0}mV, AE = {1}mV".format(round(ox_w_raw,3), round(ox_a_raw,3))
		print "CO:     WE = {0}mV, AE = {1}mV".format(round(co_w_raw,3), round(co_a_raw,3))
		print "NO:     WE = {0}mV, AE = {1}mV".format(round(no_w_raw,3), round(no_a_raw,3))
		print ""
		
		print "PM Measurements:"
		pm_data = opcn3.histogram()
		pm2_5 = pm_data['PM_B']
		pm10 = pm_data['PM_C']
		csv_row['pm2.5'] = round(pm2_5,3)
		csv_row['pm10'] = round(pm10,3)

		
		print "PM  2.5: {0}{1}g/m{2}".format(round(pm2_5,2), u'\u00B5'.encode('utf8'), u'\u00B3'.encode('utf8'))
		print "PM 10.0: {0}{1}g/m{2}".format(round(pm10,2), u'\u00B5'.encode('utf8'), u'\u00B3'.encode('utf8'))
		print "****************************************"
		print ""
		
		# Write row to local CSV file
		writer.writerow(csv_row)
		
		# Create message payload
		payload = {"state":{"reported":csv_row}}

		# Update shadow
		deviceShadowHandler.shadowUpdate(json.dumps(payload), shadow_callback_update, 5)
		
		
# Function called when a shadow is updated
def shadow_callback_update(payload, response_status, token):

    # Display status and data from update request
    if response_status == "timeout":
        print "Update request " + token + " time out!"

    if response_status == "accepted":
        payloadDict = json.loads(payload)
        print "~~~~~~~~~~~~~~~~~~~~~~~" 
        print "Update request with token: " + token + " accepted!" 
        print "~~~~~~~~~~~~~~~~~~~~~~~\n\n"

    if response_status == "rejected":
        print "Update request " + token + " rejected!"


# Function called when a shadow is deleted
def shadow_callback_delete(payload, response_status, token):

     # Display status and data from delete request
    if response_status == "timeout":
        print "Delete request " + token + " time out!"

    if response_status == "accepted":
        print "~~~~~~~~~~~~~~~~~~~~~~~"
        print "Delete request with token: " + token + " accepted!"
        print "~~~~~~~~~~~~~~~~~~~~~~~\n\n"

    if response_status == "rejected":
        print "Delete request " + token + " rejected!"


# Configure logging
# AWSIoTMQTTShadowClient writes data to the log
def configureLogging():

    logger = logging.getLogger("AWSIoTPythonSDK.core")
    logger.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)
	


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

# Create local output CSV file
now = datetime.datetime.now().strftime("%d%m%Y-%H%M")
f = open("/home/pi/outdoor-node/data/node" + str(node_id) + "_" + now + ".csv", 'w+')
fnames = ['timestamp', 'temperature', 'humidity', 'pm2.5', 'pm10', 'so2_we', 'so2_ae', 'no2_we', 'no2_ae', 'ox_we', 'ox_ae', 'co_we', 'co_ae', 'no_we', 'no_ae']
writer = csv.DictWriter(f, fieldnames=fnames)  
writer.writeheader()
f.close()

# Init AWSIoTMQTTShadowClient
myAWSIoTMQTTShadowClient = None
myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(client_id)
myAWSIoTMQTTShadowClient.configureEndpoint(endpoint, port)
myAWSIoTMQTTShadowClient.configureCredentials(root_CA_path, priv_key_path, cert_path)

# AWSIoTMQTTShadowClient connection configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10) # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5) # 5 sec

# Connect to AWS IoT
myAWSIoTMQTTShadowClient.connect()

# Create a device shadow handler, use this to update and delete shadow document
deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thing_name, True)

# Delete current shadow JSON doc
deviceShadowHandler.shadowDelete(shadow_callback_delete, 5)

# Loop for taking measurements from sensors, stop with CTRL+C
proceed = True
while proceed == True:
	try:
		# Take measurements from sensors
		datapoints = get_data()
		
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
