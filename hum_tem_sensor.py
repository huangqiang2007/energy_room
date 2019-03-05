#!/usr/bin/python3
#
# File name: hum_tem_sensor.py
# Author: huangq@moxigroup.com
#
# Note: this file is the main logic for serial(UART) operation.
#
#
#
#
import serial
import time
from dbg import *

sensor_cmd = '01 03 00 00 00 02 C4 0B'
sensor_cmd__bytes = bytes.fromhex(sensor_cmd)
def ser_open():
	global ser
	ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.1)

def ser_close():
	global ser
	ser.close()

def ser_read():
	global ser
	ser.write(sensor_cmd__bytes)
	p_dbg(DBG_DEBUG, '\nwrite: ' + str(sensor_cmd__bytes))
	time.sleep(0.2)
	n = ser.inWaiting()
	if n != 0:
		data = ser.readline()
		ser.flushInput()
		if n != len(data):
			p_dbg(DBG_ERROR, "recv: {} bytes, actual: {} bytes".format(n, len(data)))
			return(-1, -1)
		humidity = (data[3] << 8) | data[4]
		humidity = humidity / 10
		if (humidity > 100):
			humidity = 100

		temperature = (data[5] << 8) | data[6]
		temperature = temperature / 10
		#print('hum: %.1f%%RH, tem: %.1f \'C' %(humidity, temperature))
		#for i in range(n):
		#	print('data[%d]: %d' %(i, data[i]))

		return (humidity, temperature)

def ser_get_sensor():
	ser_open()
	p_dbg(DBG_DEBUG, "ser_get_sensor()\n")
	while (True):
		(hum, tem) = ser_read()
		if hum == -1 and tem == -1:
			p_dbg(DBG_ERROR, "hum: {:.1f}%%RH, tem: {:.1f}\'C".format(hum, tem))
			continue
		else:
			break

		time.sleep(1)

	return (hum, tem)

def ser_poll(interval):
	while True:
		(hum, tem) = ser_read()
		if hum != -1 and tem != -1:
			p_dbg(DBG_INFO, "hum: {.1f}%%RH, tem: {.1f}\'C".format(hum, tem))
			continue

		time.sleep(interval)


def say_hello():
	print("say hello\n")


if __name__ == '__main__':
#ser_open()
#	ser_poll(2)
	ser_get_sensor()
