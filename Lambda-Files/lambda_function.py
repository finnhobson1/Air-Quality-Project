"""This code writes data from IoT core rule via Lambda into InfluxDB"""

import json
import os
from influxdb import InfluxDBClient

def lambda_handler(event, context):
    
    # Get measurements from AWS IoT JSON
    timestamp = event['timestamp']
    node_id = event['node_id']
    temperature = event['temperature']
    humidity = event['humidity']
    pm2_5 = event['pm2_5']
    pm10 = event['pm10']
    so2_we = event['so2_we']
    so2_ae = event['so2_ae']
    no2_we = event['no2_we']
    no2_ae = event['no2_ae']
    ox_we = event['ox_we']
    ox_ae = event['ox_ae']
    co_we = event['co_we']
    co_ae = event['co_ae']
    no_we = event['no_we']
    no_ae = event['no_ae']
    
    node_name = "Node " + str(node_id)
    
    # Set InfluxDB parameters
    host = os.environ['INFLUXDBHOST']
    port = os.environ['INFLUXDBPORT']
    user = os.environ['INFLUXDBUSR']
    password = os.environ['INFLUXDBPWD']
    dbname = os.environ['INFLUXDBNAME']
    
    client = InfluxDBClient(host, port, user, password, dbname)
    
    datapoints = [
        {
            "measurement": "air-quality-data",
            "tags": {
                "node_id": node_id
            },
            "time": timestamp,
            "fields": {
                "temperature_value": temperature,
                "humidity_value": humidity,
                "pm2_5_value": pm2_5,
                "pm10_value": pm10,
                "so2_we_value": so2_we,
                "so2_ae_value": so2_ae,
                "no2_we_value": no2_we,
                "no2_ae_value": no2_ae,
                "ox_we_value": ox_we,
                "ox_ae_value": ox_ae,
                "co_we_value": co_we,
                "co_ae_value": co_ae,
                "no_we_value": no_we,
                "no_ae_value": no_ae
            }
        }]
        
    print "Executing InfluxDB insert..."
    
    result = client.write_points(datapoints)
    
    print "Finished executing. Result: {0}".format(result)
    
