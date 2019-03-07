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

j_dic = {}

hum_tem_dic = {}
time_dic = {}
heat_dic = {}
misc_dic = {}

client=socket.socket()
client.connect(('localhost',9999))

def get_hum_tem():
	hid = input("humidify\nid: ")
	hopcode = input("opcode: ")
	hum_tem_dic["id"] = int(hid)
	hum_tem_dic["opcode"] = int(hopcode)
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

def set_time():
	hid = input("timer\nid: ")
	hopcode = input("opcode: ")
	hval = input("value: ")
	time_dic["id"] = int(hid)
	time_dic["opcode"] = int(hopcode)
	time_dic["value"] = int(hval)
	client.send(str.encode(json.dumps(time_dic)))

def recv_thread(client):
	print("recv_thread()\n")
	while (True):
		dic_res = client.recv(1024)
		print("\nrcv: " + dic_res.decode() + "\n")

thrd = Thread(target = recv_thread, args = (client,))
thrd.setDaemon(True)
thrd.start()

while True:
	jid = input("1. humidify 2. heat 3. timer\nwhich one? > ")
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
	else:
		print("no item {}\n".format(i_id))
		continue


client.close()
