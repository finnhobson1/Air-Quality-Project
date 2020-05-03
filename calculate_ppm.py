"""
This script calculates temperature corrected gas concentrations from the voltage outputs of the Alphasense B4 electrochemical sensors.

Correction Algorithms:
 1) WEc = (WEu - WEe) - nT * (AEu - AEe)
 2) WEc = (WEu - WEe) - nT * (WEo/AEo) * (AEu - AEe)
 3) WEc = (WEu - WEe) - (WEo - AEo) - nT * (AEu - AEe)
 4) WEc = (WEu - WEe) - WEo - nT

where:
	WEc = corrected WE output
	WEu = uncorrected raw WE output
	AEu = uncorrected raw AE output
	WEe = WE electronic offset on the ISB
	AEe = AE electronic offset on the ISB
	WEo = WE sensor zero (output in zero air)
	AEo = AE sensor zero (output in zero air)
	nT  = temperature dependent correction factor 

Suggested Correction Algorithm:
 SO2: 		4
 NO2: 		1
 NO2+O3:	1
 CO: 		1
 NO: 		2
"""

from ADCPi import ADCPi


# Setup ADCs for gas sensors
adc1 = ADCPi(0x68, 0x69, 16) 	# Channels: SO2 (1-2), NO2 (3-4), NO2+O3 (5-6), 
adc2 = ADCPi(0x6A, 0x6B, 16)	# Channels: CO (1-2) , NO (3-4)


so2_w_raw = adc1.read_voltage(1) * 1000
so2_a_raw = adc1.read_voltage(2) * 1000
so2_w_offset = 341
so2_a_offset = 291
so2_w_zero = 378
so2_a_zero = 362
so2_convert = 0.330

no2_w_raw = adc1.read_voltage(3) * 1000
no2_a_raw = adc1.read_voltage(4) * 1000
no2_w_offset = 224
no2_a_offset = 226
no2_w_zero = 220
no2_a_zero = 224
no2_convert = 0.223

ox_w_raw = adc1.read_voltage(5) * 1000
ox_a_raw = adc1.read_voltage(6) * 1000
ox_w_offset = 227
ox_a_offset = 219
ox_w_zero = 220
ox_a_zero = 215
ox_convert = 0.334

co_w_raw = adc1.read_voltage(1) * 1000
co_a_raw = adc1.read_voltage(2) * 1000
co_w_offset = 360
co_a_offset = 344
co_w_zero = 362
co_a_zero = 335
co_convert = 0.444

no_w_raw = adc2.read_voltage(3) * 1000
no_a_raw = adc2.read_voltage(4) * 1000
no_w_offset = 291
no_a_offset = 248
no_w_zero = 344
no_a_zero = 310
no_convert = 0.604

print "EC Sensor Raw Voltages:"
print "SO2:    WE = {0}mV, AE = {1}mV".format(round(so2_w_raw,3), round(so2_a_raw,3))
print "NO2:    WE = {0}mV, AE = {1}mV".format(round(no2_w_raw,3), round(no2_a_raw,3))
print "NO2+O3: WE = {0}mV, AE = {1}mV".format(round(ox_w_raw,3), round(ox_a_raw,3))
print "CO:     WE = {0}mV, AE = {1}mV".format(round(co_w_raw,3), round(co_a_raw,3))
print "NO:     WE = {0}mV, AE = {1}mV".format(round(no_w_raw,3), round(no_a_raw,3))
print ""


#temp = 19.0

##so2_temp_factor = -4 + (temp%10) * 0.1 * (0 - (-4))
#so2_temp_factor = 1.6
#no2_temp_factor = 1 + (temp%10) * 0.1 * (0.6 - 1)
#ox_temp_factor = 1.5 + (temp%10) * 0.1 * (1.7 - 1.5)
#co_temp_factor = 1 + (temp%10) * 0.1 * (3 - 1)
#no_temp_factor = 1.1 + (temp%10) * 0.1 * (1 - 1.1)

#print "Temperature Dependent Correction Factors:"
#print "SO2:    {0}".format(so2_temp_factor)
#print "NO2:    {0}".format(no2_temp_factor)
#print "NO2+O3: {0}".format(ox_temp_factor)
#print "CO:     {0}".format(co_temp_factor)
#print "NO:     {0}".format(no_temp_factor)
#print ""

#so2_corrected = (so2_w_raw - so2_w_zero) - (so2_a_raw - so2_a_zero)
##so2_corrected = (so2_w_raw - so2_w_offset) - so2_temp_factor * (so2_a_raw - so2_a_offset)
#no2_corrected = (no2_w_raw - no2_w_offset) - no2_temp_factor * (no2_a_raw - no2_a_offset)
#ox_corrected = (ox_w_raw - ox_w_offset) - ox_temp_factor * (ox_a_raw - ox_a_offset)
#co_corrected = (co_w_raw - co_w_offset) - co_temp_factor * (co_a_raw - co_a_offset)
#no_corrected = (no_w_raw - no_w_offset) - no_temp_factor * (no_w_zero/no_a_zero) * (no_a_raw - no_a_offset)

#print "Temperature Corrected WE Outputs:"
#print "SO2:    {0}mV".format(round(so2_corrected,3))
#print "NO2:    {0}mV".format(round(no2_corrected,3))
#print "NO2+O3: {0}mV".format(round(ox_corrected,3))
#print "CO:     {0}mV".format(round(co_corrected,3))
#print "NO:     {0}mV".format(round(no_corrected,3))
#print ""

#so2_ppm = so2_corrected / so2_convert
#no2_ppm = no2_corrected / no2_convert
#ox_ppm = ox_corrected / ox_convert
#co_ppm = co_corrected / co_convert
#no_ppm = no_corrected / no_convert

so2_ppm = ((so2_w_raw - so2_w_zero) - (so2_a_raw - so2_a_zero)) / so2_convert
no2_ppm = ((no2_w_raw - no2_w_zero) - (no2_a_raw - no2_a_zero)) / no2_convert
ox_ppm = ((ox_w_raw - ox_w_zero) - (ox_a_raw - ox_a_zero)) / ox_convert
co_ppm = ((co_w_raw - co_w_zero) - (co_a_raw - co_a_zero)) / co_convert
no_ppm = ((no_w_raw - no_w_zero) - (no_a_raw - no_a_zero)) / no_convert

print "Concentrations (No Temperature Correction):"
print "SO2:    {0}ppm".format(int(so2_ppm))
print "NO2:    {0}ppm".format(int(no2_ppm))
print "NO2+O3: {0}ppm".format(int(ox_ppm))
print "CO:     {0}ppm".format(int(co_ppm))
print "NO:     {0}ppm".format(int(no_ppm))
print ""
