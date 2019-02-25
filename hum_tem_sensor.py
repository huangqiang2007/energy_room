#!/usr/bin/python3

import serial
import time

a = '01 03 00 00 00 02 C4 0B'
a_bytes = bytes.fromhex(a)
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.1)

while True:
	ser.write(a_bytes)
	print('\nwrite: ' + str(a_bytes))
	time.sleep(0.2)
	n = ser.inWaiting()
	if n != 0:
		data = ser.readline()
		ser.flushInput()
		if n != len(data):
			print("recv: {} bytes, actual: {} bytes".format(n, len(data)))
			continue
		humidity = (data[3] << 8) | data[4]
		humidity = humidity / 10

		temperature = (data[5] << 8) | data[6]
		temperature = temperature / 10
		print('hum: %.1f%%, tem: %.1f \'C' %(humidity, temperature))
		for i in range(n):
			print('data[%d]: %d' %(i, data[i]))

	time.sleep(2)
