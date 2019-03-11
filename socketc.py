#!/usr/bin/python3
#
# File name: socketc.py
# Author: huangq@moxigroup.com
#
# Note: this file is the main logic for client connection, it
# acts as an GUI input interface. Then it's responsible for
# pasing packets to server side.
#
#
from threading import Timer, Condition, Thread
import socket
import json
import struct
import fcntl
import time

j_dic = {}

hum_tem_dic = {}
time_dic = {}
heat_dic = {}
misc_dic = {}
sw_dic = {}

def get_ip_address(ip_name):
	sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	ip_addr = socket.inet_ntoa(fcntl.ioctl(sk.fileno(), 0x8915, \
		struct.pack('256s', ip_name[:15]))[20:24])
	print("ip: {}\n".format(ip_addr))
	return ip_addr

ip = get_ip_address(str.encode("eth0"))
client=socket.socket()
client.connect((ip,9998))

def get_hum_tem():
	hid = input("humidify\nid: ")
	hopcode = input("opcode: ")
	hum_tem_dic["id"] = int(hid)
	hum_tem_dic["opcode"] = int(hopcode)
	client.send(str.encode(json.dumps(hum_tem_dic)))

def get_hum_tem_poll():
	hum_tem_dic["id"] = 1
	hum_tem_dic["opcode"] = 1
	client.send(str.encode(json.dumps(hum_tem_dic)))

def set_heat():
	hid = input("heatfilm\nid: ")
	hopcode = input("opcode: ")
	hzone = input("zone: ")
	hval = input("value: ")
	heat_dic["id"] = int(hid)
	heat_dic["opcode"] = int(hopcode)
	heat_dic["zone"] = int(hzone)
	heat_dic["value"] = int(hval)
	client.send(str.encode(json.dumps(heat_dic)))

def set_heat_film(id1, opcode, zone, value):
	heat_dic["id"] = id1
	heat_dic["opcode"] = opcode
	heat_dic["zone"] = zone
	heat_dic["value"] = value
	client.send(str.encode(json.dumps(heat_dic)))

def set_time():
	hid = input("timer\nid: ")
	hopcode = input("opcode: ")
	hval = input("value: ")
	time_dic["id"] = int(hid)
	time_dic["opcode"] = int(hopcode)
	time_dic["value"] = int(hval)
	client.send(str.encode(json.dumps(time_dic)))

def set_heat_time(id1, opcode, value):
	time_dic["id"] = id1
	time_dic["opcode"] = opcode
	time_dic["value"] = value
	client.send(str.encode(json.dumps(time_dic)))

def set_filmswitch(id1, opcode, zone, value):
	sw_dic["id"] = id1
	sw_dic["opcode"] = opcode
	sw_dic["zone"] = zone
	sw_dic["value"] = value
	client.send(str.encode(json.dumps(sw_dic)))

def recv_thread(client):
	print("recv_thread()\n")
	while (True):
		dic_res = client.recv(1024)
		print("\nrcv: " + dic_res.decode() + "\n")

def poll_humtem_thread(client):
	print("poll_humtem_thread()\n")
	while (True):
		get_hum_tem_poll()
		time.sleep(10)

def heat_film_thread(client):
	while (True):
		print("heat_film_thread() run ...\n")
		set_heat_film(2, 1, 0, 1)
		set_heat_film(2, 1, 1, 2)
#		set_heat_film(2, 1, 2, 1)
#		set_heat_film(2, 1, 3, 3)
		set_heat_time(3, 1, 30)
		set_filmswitch(5, 1, 0, 1)
		set_filmswitch(5, 1, 1, 1)

		time.sleep(60)


rcv_thrd = Thread(target = recv_thread, args = (client,))
rcv_thrd.setDaemon(True)
rcv_thrd.start()

hum_thrd = Thread(target = poll_humtem_thread, args = (client,))
hum_thrd.setDaemon(True)
hum_thrd.start()

heat_thrd = Thread(target = heat_film_thread, args = (client,))
heat_thrd.setDaemon(True)
heat_thrd.start()

while True:
	jid = input("1. humidify 2. heat 3. timer, 5. zoneswitch\nwhich one? > ")
	if (jid < '0' or jid > '9'):
		continue

	i_id = int(jid)
	if (i_id == 0):
		break

	if (i_id == 1):
		get_hum_tem()
	elif (i_id == 2):
		set_heat()
	elif (i_id == 3):
		set_time()
	elif (i_id == 4):
		print("4\n")
	elif (i_id == 5):
		set_filmswitch(5, 1, 0, 0)
#		set_filmswitch(5, 1, 1, 0)

	else:
		print("no item {}\n".format(i_id))
		continue


client.close()
