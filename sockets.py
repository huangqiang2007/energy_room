#!/usr/bin/env python3
#
# File name: sockets.py
# Author: huangq@moxigroup.com
#
# Note: this file is the main logic for server, it
# wait and receive packets coming from client(UI level).
# then it's responsible for parsing packets and handle them.
#
#
#
from threading import Timer, Condition, Thread
import socketserver
import queue
import json
import hum_tem_sensor as hts
import pwm_for_film as pwm
from dbg import *

#
# opcode
#
OP_GET = 0
OP_SET = 1

#
# heat film zone
#
ZONE_LEFT_RIGHT = 0
ZONE_BACK = 1
ZONE_BOTTOM = 2

#
# state feedback
#
STATE_SUCCESS = 1
STATE_FAIL = 0

#
# event packet type
#
PT_SENSOR = 0x01
PT_HEATFILM = 0x02
PT_TIME = 0x04
PT_MISC = 0x08

#
# device subtype for PT_MISC packet type
#
# 0 - time, 1 - lamp, 2 - read light, 3 - humidifier, 4 - fan, 5 - oxygen bar, 6 - speaker
#
ST_TIME = 0
ST_LAMP = 1
ST_READLIGHT = 2
ST_HUMIDIFIER = 3
ST_FAN = 4
ST_OBAR = 5
ST_SPEAKER = 6

#
# device  status record array
#
# [device_idx, value/status]
#
device_status = [ \
	[ST_TIME, 30], \
	[ST_LAMP, 0], \
	[ST_READLIGHT, 0], \
	[ST_HUMIDIFIER, 0], \
	[ST_FAN, 0], \
	[ST_OBAR, 0], \
	[ST_SPEAKER, 0], \
]

#
# initial
#
j_dic = {}
con = Condition()
in_q = queue.Queue(10)


class MiscDeviceHandle:

	def __init__(self, request):
		p_dbg(DBG_INFO, "MiscDeviceHandle()\n")
		self.request = request
		# the heat time interval correspond to low level heating
		self.heat_timer_period = 30
		self.heat_timer = Timer(self.heat_timer_period * 60, self.heatTimerCb, ())

	def dump_device_status(self):
		for i in range(len(device_status)):
			print("d_s[{0}][1] = {1}\n".format(i, device_status[i][1]))
	#
	# the timer callback function for heating film
	#
	def heatTimerCb(self):
		global device_status
		device_status[ST_TIME][1] = 0
		print("heatTImerCb()\n")
		pwm.pwm_stopAll()
		self.request.sendall(str.encode("heatTimerCb()\n"))

	def __handle_lamp(self, json_dic):
		print("__handle_lamp()\n")

	def __handle_readlight(self, json_dic):
		print("__handle_readlight()\n")

	def __handle_humidifier(self, json_dic):
		print("__handle_humidifier()\n")

	def __handle_fan(self, json_dic):
		print("__handle_fan()\n")

	def __handle_obar(self, json_dic):
		print("__handle_obar()\n")

	def __handle_speaker(self, json_dic):
		print("__handle_speaker()\n")

	def handle_misc_device(self, json_dic):
		j_device = int(json_dic["device"])
		if (j_device == ST_LAMP):
			__handle_lamp(json_dic)

		elif (j_device == ST_READLIGHT):
			__handle_readlight(json_dic)

		elif (j_device == ST_HUMIDIFIER):
			__handle_humidifier(json_dic)

		elif (j_device == ST_FAN):
			__handle_fan(json_dic)

		elif (j_device == ST_OBAR):
			__handle_obar(json_dic)

		elif (j_device == ST_SPEAKER):
			__handle_speaker(json_dic)

		else:
			p_dbg(DBG_ERROR, "can't know device: {}\n".format(j_device))


#
# this class is responsible for parse all packets
# which come from client(UI input)
#
class MessageParser:

	def __init__(self, request):
		self.request = request
		self.miscDeviceHandle = MiscDeviceHandle(request)
		p_dbg(DBG_INFO, "init messageparser\n")

	def send_test(self):
		print ("+ send_test ...\n")
		self.request.sendall(str("hello world\n").encode())
		print ("- send_test ...\n")

	# the private function with '__' prefix
	def __handle_sensor(self, json_dic):
		(hum, tem) = hts.ser_get_sensor()
		json_dic["hum"] = hum
		json_dic["tem"] = tem
		p_dbg(DBG_DEBUG, "id = {:d}, type = {:d}, value = {:d}, hum = {:.1f}, tem = {:.1f}\n".format(json_dic["id"], json_dic["type"], json_dic["value"], json_dic["hum"], json_dic["tem"]))
		self.request.sendall(str.encode(json.dumps(json_dic)))

	def __handle_heatfilm(self, json_dic):
		p_dbg(DBG_DEBUG, "msg id: {}\n".format(json_dic["id"]))
		self.request.sendall(str.encode("__handle_heatfilm()\n"))

	def __handle_time(self, json_dic):
		global heat_timer
		p_dbg(DBG_DEBUG, "msg id: {}, time: {}\n".format(json_dic["id"], json_dic["value"]))
		self.miscDeviceHandle.dump_device_status()
		device_status[ST_TIME][1] = int(json_dic["value"])
		self.miscDeviceHandle.dump_device_status()
		self.miscDeviceHandle.heat_timer.cancel()
		self.miscDeviceHandle.heat_timer = Timer(device_status[ST_TIME][1], \
			self.miscDeviceHandle.heatTimerCb, ())
		self.miscDeviceHandle.heat_timer.start()
		self.request.sendall(str.encode("__handle_time()\n"))

	def __handle_misc(self, json_dic):
		p_dbg(DBG_DEBUG, "msg id: {}\n".format(json_dic["id"]))
		self.miscDeviceHandle.handle_misc_device(json_dic)
		self.request.sendall(str.encode("__handle_misc()\n"))

	#
	# parse all UI sented packets and handle them seperately
	#
	def parseMessage(self, json_dic):
		p_dbg(DBG_DEBUG, "parseMessage()\n")
		j_id = json_dic["id"]
		if (j_id == PT_SENSOR):
			self.__handle_sensor(json_dic)

		elif (j_id == PT_HEATFILM):
			self.__handle_heatfilm(json_dic)

		elif (j_id == PT_TIME):
			self.__handle_time(json_dic)

		elif (j_id == PT_MISC):
			self.__handle_misc(json_dic)

		else:
			p_dbg(DBG_ERROR, "can't parse id: {}".format(json_dic["id"]))
			self.request.sendall(str.encode("can't parse id: {}".format(json_dic["id"])))

#
# fetch each message from queue and parse it
#
def consume_queue():
	global message_parser
	p_dbg(DBG_DEBUG, "consume_queue()\n")
	j_dic_str = in_q.get()
	j_dic = json.loads(j_dic_str)
	message_parser.parseMessage(j_dic)

#
# one specific thread for consuming message queue
# @con: Condition variable
#
def consum_thread(con):
	p_dbg(DBG_DEBUG, "consum_thread()\n")
	while(True):
		if(in_q.empty() == True):
			p_dbg(DBG_INFO, "consumer waiting ...\n")
			con.acquire()
			con.wait()
			con.release()
			p_dbg(DBG_INFO, "consumer run again ...\n")
		else:
			consume_queue()

#
# a socket server handler class needed by socketserver
#
class SockTCPHandler(socketserver.BaseRequestHandler):

	def handle(self):
		global message_parser
		try:
			while True:
				self.data = self.request.recv(1024)
				p_dbg(DBG_INFO, "{} send: {}\n".format(self.client_address, self.data))
				if not self.data:
					p_dbg(DBG_ERROR, "connection lost")
					break

				j_str = bytes.decode(self.data)
				con.acquire()
				in_q.put(j_str)
				con.notify()
				con.release()

				#self.request.sendall(str.encode(ht_str))
		except Exception as e:
			p_dbg(DBG_ERROR, "{}, {}".format(self.client_address, "exception error"))
		finally:
			self.request.close()
	def setup(self):
		global message_parser
		message_parser = MessageParser(self.request)
		p_dbg(DBG_ALERT, "connect setup() {}\n".format(self.client_address))
	def finish(self):
		p_dbg(DBG_ALERT, "connect finish()\n")

if __name__ == "__main__":
	HOST,PORT = "localhost",9999
	Thread(target = consum_thread, args = (con,)).start()
	server = socketserver.TCPServer((HOST,PORT), SockTCPHandler)
	server.serve_forever()
