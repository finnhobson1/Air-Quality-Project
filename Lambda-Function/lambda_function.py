"""This code writes data from IoT core rule via Lambda into InfluxDB"""

import json
import os
import boto3
from influxdb import InfluxDBClient


# Setup DynamoDB table for Read operations
dynamodb = boto3.resource("dynamodb", region_name='eu-west-2')
table = dynamodb.Table('Sensor-Information')

    
def calculate_so2(node_id, we_raw, temp):
    
    # Get calibration values from DynamoDB lookup table
    calibration_values = table.get_item(Key={'node_id': node_id})
    
    we_offset = float(calibration_values['Item']['so2_we_offset'])
    we_zero = float(calibration_values['Item']['so2_we_zero'])
    temp_factors = calibration_values['Item']['so2_temp_factor']
    sensitivity = float(calibration_values['Item']['so2_sensitivity'])
    
    index = int((temp + 30)//10)
    temp_factor = float(temp_factors[index]) + (temp%10) * 0.1 * (float(temp_factors[index+1]) - float(temp_factors[index]))
    
    we_corrected = (we_raw - we_offset) - we_zero - temp_factor
    estimate = we_corrected/sensitivity

    if estimate < 0:
        estimate = 0
    
    return round(estimate,3)
    
    
def calculate_no2(node_id, we_raw, ae_raw, temp):

    # Get calibration values from DynamoDB lookup table
    calibration_values = table.get_item(Key={'node_id': node_id})
    
    we_offset = float(calibration_values['Item']['no2_we_offset'])
    ae_offset = float(calibration_values['Item']['no2_ae_offset'])
    temp_factors = calibration_values['Item']['no2_temp_factor']
    sensitivity = float(calibration_values['Item']['no2_sensitivity'])
    
    index = int((temp + 30)//10)
    temp_factor = float(temp_factors[index]) + (temp%10) * 0.1 * (float(temp_factors[index+1]) - float(temp_factors[index]))
    
    we_corrected = (we_raw - we_offset) - temp_factor * (ae_raw - ae_offset)
    estimate = we_corrected/sensitivity
    
    if estimate < 0:
        estimate = 0
    
    return round(estimate,3)
    
    
def calculate_o3(node_id, we_raw, ae_raw, temp, no2_estimate):
    
    # Get calibration values from DynamoDB lookup table
    calibration_values = table.get_item(Key={'node_id': node_id})
    
    we_offset = float(calibration_values['Item']['ox_we_offset'])
    ae_offset = float(calibration_values['Item']['ox_ae_offset'])
    temp_factors = calibration_values['Item']['ox_temp_factor']
    sensitivity = float(calibration_values['Item']['ox_sensitivity'])
    
    index = int((temp + 30)//10)
    temp_factor = float(temp_factors[index]) + (temp%10) * 0.1 * (float(temp_factors[index+1]) - float(temp_factors[index]))
    
    we_corrected = (we_raw - we_offset) - temp_factor * (ae_raw - ae_offset)
    no2_o3_estimate = we_corrected/sensitivity
    estimate = no2_o3_estimate - no2_estimate

    if estimate < 0:
        estimate = 0
    
    return round(estimate,3)
    
    
def calculate_co(node_id, we_raw, ae_raw, temp):
    
    # Get calibration values from DynamoDB lookup table
    calibration_values = table.get_item(Key={'node_id': node_id})
    
    we_offset = float(calibration_values['Item']['co_we_offset'])
    ae_offset = float(calibration_values['Item']['co_ae_offset'])
    temp_factors = calibration_values['Item']['co_temp_factor']
    sensitivity = float(calibration_values['Item']['co_sensitivity'])
    
    index = int((temp + 30)//10)
    temp_factor = float(temp_factors[index]) + (temp%10) * 0.1 * (float(temp_factors[index+1]) - float(temp_factors[index]))
    
    we_corrected = (we_raw - we_offset) - temp_factor * (ae_raw - ae_offset)
    estimate = we_corrected/sensitivity
    
    if estimate < 0:
        estimate = 0
    
    return round(estimate,3)
    

def calculate_no(node_id, we_raw, ae_raw, temp):
    
    # Get calibration values from DynamoDB lookup table
    calibration_values = table.get_item(Key={'node_id': node_id})
    
    we_offset = float(calibration_values['Item']['no_we_offset'])
    ae_offset = float(calibration_values['Item']['no_ae_offset'])
    we_zero = float(calibration_values['Item']['no_we_zero'])
    ae_zero = float(calibration_values['Item']['no_ae_zero'])
    temp_factors = calibration_values['Item']['no_temp_factor']
    sensitivity = float(calibration_values['Item']['no_sensitivity'])
    
    index = int((temp + 30)//10)
    temp_factor = float(temp_factors[index]) + (temp%10) * 0.1 * (float(temp_factors[index+1]) - float(temp_factors[index]))
    
    we_corrected = (we_raw - we_offset) - temp_factor * (we_zero/ae_zero) * (ae_raw - ae_offset)
    
    estimate = we_corrected/sensitivity
    
    if estimate < 0:
        estimate = 0
    
    return round(estimate,3)
    

def lambda_handler(event, context):
    
    # Get measurements from AWS IoT JSON
    timestamp = event['timestamp']
    node_id = event['node_id']
    #geohash = event['geohash']
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
    
    so2_estimate = calculate_so2(node_id, so2_we, temperature)
    no2_estimate = calculate_no2(node_id, no2_we, no2_ae, temperature)
    o3_estimate = calculate_o3(node_id, ox_we, ox_ae, temperature, no2_estimate)
    co_estimate = calculate_co(node_id, co_we, co_ae, temperature)
    no_estimate = calculate_no(node_id, no_we, no_ae, temperature)

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
                #"geohash": geohash,
                "temperature": temperature,
                "humidity": humidity,
                "pm2_5": pm2_5,
                "pm10": pm10,
                "so2_raw": so2_we,
                "so2_aux_raw": so2_ae,
                "so2_estimate": so2_estimate,
                "no2_raw": no2_we,
                "no2_aux_raw": no2_ae,
                "no2_estimate": no2_estimate,
                "o3_raw": ox_we,
                "o3_aux_raw": ox_ae,
                "o3_estimate": o3_estimate,
                "co_raw": co_we,
                "co_aux_raw": co_ae,
                "co_estimate": co_estimate,
                "no_raw": no_we,
                "no_aux_raw": no_ae,
                "no_estimate": no_estimate
            }
        }]
        
    print "Executing InfluxDB insert..."
    
    result = client.write_points(datapoints)
    
    print "Finished executing. Result: {0}".format(result)
    
