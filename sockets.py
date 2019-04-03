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
import sys
import queue
import json
import socket
import struct
import re
import fcntl
import wiringpi as wp
import hum_tem_sensor as hts
import pwm_for_film as pwm
import misc_dev as misc
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
ZONE_OTHER = 3

#
# heating level
#
HEAT_ZERO = 0
HEAT_LOW = 1
HEAT_MID = 2
HEAT_HIGH = 3

#
# heatfile zone status record
#
# [zone, level, status]
#
heatzone_status = [ \
	[ZONE_LEFT_RIGHT, HEAT_ZERO, False], \
	[ZONE_BACK, HEAT_ZERO, False], \
	[ZONE_BOTTOM, HEAT_ZERO, False], \
	[ZONE_OTHER, HEAT_ZERO, False] \
]

#
# pwm period 100us unit
# eg: 1000 * 100us = 100ms
#
PWM_PERIOD = 1000

#
# pwm duty step
#
# low level heat 300 * 1 = 300, duty ratio 30%
# mid level heat 300 * 2 = 600, duty ratio 60%
# high level heat 300 * 3 = 900, duty ratio 90%
#
PWM_DUTY_STEP = 300

#
# state feedback
#
STATE_SUCCESS = 1
STATE_FAIL = 0

#
# switch state
#
SW_ON = 1
SW_OFF = 0

#
# event packet type
#
PT_SENSOR = 0x01
PT_HEATFILM = 0x02
PT_TIME = 0x03
PT_MISC = 0x04
PT_FILMSWITCH = 0x05

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
message_queue = queue.Queue(20)
re_rule = re.compile(r'\{.*?\}+')
g_server = None
message_parser = None

#
# if there's no sensor packets coming more than
# (g_hearttimer_period) seconds, it indicates network
# is offline, then disable heating logic
#
g_hearttimer_period = 60

#
# to avoid the case that due to network issue, it can't receive
# shutdown command when the time period for heating is over.
# it sets a timer with interval (setted heating time + g_heat_timeout),
# if this timer is invoked, it has to stop heating logic anyway.
#
g_heat_timeout = 120

#
# this class is the detail implementation for handling detail of misc device.
#
class MiscDeviceHandle:

	def __init__(self, request):
		p_dbg(DBG_INFO, "MiscDeviceHandle()\n")
		self.request = request
		self.timerinit = 0
		self.timerenable = 0
		# the heat time interval correspond to low level heating
		self.heat_timer_period = 30
		self.heat_timer = Timer(self.heat_timer_period * 60, self.heatTimerCb, ())
		misc.misc_init()

	def dump_device_status(self):
		for i in range(len(device_status)):
			print("d_s[{0}][1] = {1}\n".format(i, device_status[i][1]))

	def __send_feedback_packet(self, json_dic, state):
		try:
			json_dic["state"] = state
			self.request.sendall(str.encode(json.dumps(json_dic)))
		except:
			p_dbg(DBG_ERROR, "MiscDeviceHandle __send_feedback_packet() error\n")

	#
	# if heat timer is not set firstly, just only save the heat level value and set the flag of heat zone.
	# if the flag of heat zone is set beforehand, config conrresponding PWM channel directly.
	#
	def set_heatfilm(self, zone, level):
		ret = 0

		# store pre-setting heat level
		heatzone_status[zone][1] = level

		if (heatzone_status[zone][2] == False):
			heatzone_status[zone][2] = True
			p_dbg(DBG_DEBUG, "set_heatfilm(): mark heat zone {}\n".format(zone))
		else:
			# only if the heat timer is enabled, the heat film's heating level 
			# can be justified.
			if (self.timerenable == 1):
				if (zone == 0):
					# left and right sides' heatfilm, need two PWM channels
					for z in range(2):
						ret = pwm.pwm_setSingleChannel(z, wp.OUTPUT, wp.LOW, PWM_PERIOD, \
							PWM_DUTY_STEP * level)
				else:
					# other sides' heatfilm
					ret = pwm.pwm_setSingleChannel(zone + 1, wp.OUTPUT, wp.LOW, PWM_PERIOD, \
						PWM_DUTY_STEP * level)

				p_dbg(DBG_DEBUG, "set_heatfilm(): config heat zone {}: period {}, duty {}\n".format( \
					zone, PWM_PERIOD, PWM_DUTY_STEP * level))
				pwm.pwm_dumpAll()

		return ret

	#
	# check if the flag of heat zone is set, if so, config the corresponding PWM channel.
	#
	def check_and_set_heatfilm(self):
		ret = 0
		for z in range(len(heatzone_status)):
			if (heatzone_status[z][2] == True):
				ret = self.set_heatfilm(z, heatzone_status[z][1])
				if (ret < 0):
					p_dbg(DBG_ERROR, "heat zone {}, config fail\n".format(z))
					return ret

		return ret

	#
	# disable all heat zones and restore status record to 'False'
	#
	def disable_allHeatZone(self):
		pwm.pwm_stopAll()
		for i in range(len(heatzone_status)):
			heatzone_status[i][2] = False

		pwm.pwm_dumpAll()

	#
	# the timer callback function for heating film
	#
	def heatTimerCb(self):
		global device_status
		p_dbg(DBG_DEBUG, "heatTImerCb()\n")

		self.timerinit = 0
		self.timerenable = 0
		self.disable_allHeatZone()

		t_dic = {}
		t_dic["id"] = PT_TIME
		t_dic["opcode"] = OP_GET
		t_dic["value"] = device_status[ST_TIME][1]
		device_status[ST_TIME][1] = 0
		self.__send_feedback_packet(t_dic, STATE_SUCCESS)

	def __handle_lamp(self, dev, state):
		p_dbg(DBG_DEBUG, "__handle_lamp()\n")
		return misc.misc_configSingleDev(dev, state)

	def __handle_readlight(self, dev, state):
		p_dbg(DBG_DEBUG, "__handle_readlight()\n")
		return misc.misc_configSingleDev(dev, state)

	def __handle_humidifier(self, dev, state):
		p_dbg(DBG_DEBUG, "__handle_humidifier()\n")
		return misc.misc_configSingleDev(dev, state)

	def __handle_fan(self, dev, state):
		p_dbg(DBG_DEBUG, "__handle_fan()\n")
		return misc.misc_configSingleDev(dev, state)

	def __handle_obar(self, dev, state):
		p_dbg(DBG_DEBUG, "__handle_obar()\n")
		return misc.misc_configSingleDev(dev, state)

	def __handle_speaker(self, dev, state):
		p_dbg(DBG_DEBUG, "__handle_speaker()\n")
		return misc.misc_configSingleDev(dev, state)

	def handle_misc_device(self, json_dic):
		try:
			j_device = int(json_dic["device"])
			state = int(json_dic["opcode"])
		except:
			p_dbg(DBG_ERROR, "handle_misc_device() parse json exception\n")
			return -2

		if (j_device == ST_LAMP):
			return self.__handle_lamp(ST_LAMP, state)

		elif (j_device == ST_READLIGHT):
			return self.__handle_readlight(ST_READLIGHT, state)

		elif (j_device == ST_HUMIDIFIER):
			return self.__handle_humidifier(ST_HUMIDIFIER, state)

		elif (j_device == ST_FAN):
			return self.__handle_fan(ST_FAN, state)

		elif (j_device == ST_OBAR):
			return self.__handle_obar(ST_OBAR, state)

		elif (j_device == ST_SPEAKER):
			return self.__handle_speaker(ST_SPEAKER, state)

		else:
			p_dbg(DBG_ERROR, "can't know device: {}\n".format(j_device))
			return -1

#
# this class is responsible for parse all packets
# which come from client(UI input)
#
class MessageParser:

	def __init__(self, request):
		self.heartbeat_timer = Timer(30, self.heartbeat_timerCb, ())
		self.request = request
		self.miscDeviceHandle = MiscDeviceHandle(request)
		p_dbg(DBG_INFO, "init messageparser\n")

	#
	# reinit socket request for each packet handling
	#
	def reinit_request(self, request):
		self.request = request
		self.miscDeviceHandle.request = request

	def __send_feedback_packet(self, json_dic, state):
		try:
			json_dic["state"] = state
			self.request.sendall(str.encode(json.dumps(json_dic)))
		except:
			p_dbg(DBG_ERROR, "MessageParser __send_feedback_packet() error\n")

	#
	# heartbeat timer call back function
	#
	def heartbeat_timerCb(self):
		p_dbg(DBG_ALERT, "heartbeat_timerCb() enter")
		self.miscDeviceHandle.heatTimerCb()
		p_dbg(DBG_ALERT, "heartbeat_timerCb() exit")

	#
	# as UI client will send sensor sample packet every 10 seconds,it
	# takes this as heartbeat detection condition. on receiving the packet,
	# it starts a timer with interval(60 seconds), if there is no such packet
	# coming again during the 60 seconds,we think there is no heartbeat(network
	# stall).we chose to stop the whole system.
	#
	def __handle_heartbeattimer(self):
		global g_hearttimer_period
		try:
			p_dbg(DBG_DEBUG, "__handle_heartbeattimer()")
			if (self.heartbeat_timer.is_alive() == True):
				self.heartbeat_timer.cancel()

			self.heartbeat_timer = Timer(g_hearttimer_period, self.heartbeat_timerCb, ())
			self.heartbeat_timer.start()
			p_dbg(DBG_DEBUG, "self.heartbeat_timer.start()")
		except:
			p_dbg(DBG_ERROR, "self.heartbeat_timer.start() fail")

	# the private function with '__' prefix
	def __handle_sensor(self, json_dic):
		(hum, tem) = hts.ser_get_sensor()
		json_dic["hum"] = hum
		json_dic["tem"] = tem
		p_dbg(DBG_DEBUG, "id = {:d}, opcode = {:d}, hum = {:.1f}, tem = {:.1f}\n".format( \
			json_dic["id"], json_dic["opcode"], json_dic["hum"], json_dic["tem"]))
		self.__send_feedback_packet(json_dic, STATE_SUCCESS)

	def __handle_heatfilm(self, json_dic):
		p_dbg(DBG_DEBUG, "msg id: {}\n".format(json_dic["id"]))
		try:
			j_zone = int(json_dic["zone"])
			j_heatlevel = int(json_dic["value"])
		except:
			p_dbg(DBG_ERROR, "__handle_heatfilm(): parse[\"zone\"] or parse[\"value\"] fail\n")
			self.__send_feedback_packet(json_dic, STATE_FAIL)
			return

		if (self.miscDeviceHandle.set_heatfilm(j_zone, j_heatlevel) < 0):
			# set fail
			self.__send_feedback_packet(json_dic, STATE_FAIL)
		else:
			# set success
			self.__send_feedback_packet(json_dic, STATE_SUCCESS)

		p_dbg(DBG_DEBUG, "__handle_heatfilm() done\n")


	def __handle_time(self, json_dic):
		p_dbg(DBG_DEBUG, "msg id: {}, time: {}\n".format(json_dic["id"], json_dic["value"]))
		try:
			device_status[ST_TIME][1] = int(json_dic["value"]) * 60 + 30
		except:
			self.__send_feedback_packet(json_dic, STATE_FAIL)
			p_dbg(DBG_ERROR, "__handle_time(): parse dic[\"value\"] fail\n")
			return

		# set a timer to detect if the period of heating film is over,
		# if so, it can disable heating logic.
		try:
			self.miscDeviceHandle.heat_timer.cancel()
		except:
			p_dbg(DBG_ERROR, "__handle_time() cancel heattimer fail\n")

		self.miscDeviceHandle.timerinit = 1
		self.miscDeviceHandle.heat_timer = Timer(device_status[ST_TIME][1], \
			self.miscDeviceHandle.heatTimerCb, ())

		if (self.miscDeviceHandle.timerenable == 1):
			self.miscDeviceHandle.heat_timer.start()
			p_dbg(DBG_INFO, "heat_timer.start()")

		self.__send_feedback_packet(json_dic, STATE_SUCCESS)

	def __handle_misc(self, json_dic):
		p_dbg(DBG_DEBUG, "msg id: {}\n".format(json_dic["id"]))
		if (self.miscDeviceHandle.handle_misc_device(json_dic) < 0):
			# fail
			self.__send_feedback_packet(json_dic, STATE_FAIL)
		else:
			# success
			self.__send_feedback_packet(json_dic, STATE_SUCCESS)

	def __handle_filmswitch(self, json_dic):
		p_dbg(DBG_DEBUG, "__handle_filmswitch()\n")
		try:
			zone = json_dic["zone"]
			on_off = json_dic["value"]
		except:
			p_dbg(DBG_ERROR, "__handle_filmswitch json parse fail\n")
			self.__send_feedback_packet(json_dic, STATE_FAIL)
			return

		if ((zone < 0 or zone > 4) or (on_off != 0 and on_off != 1)):
			p_dbg(DBG_ALERT, "zone or switch value invalid\n")
			self.__send_feedback_packet(json_dic, STATE_FAIL)
			return

		if (on_off == SW_ON):
			# get the pre-setting heat level
			heatlevel = heatzone_status[zone][1]
			if (heatlevel <= 0 or heatlevel > 3):
				p_dbg(DBG_ERROR, "invalid heat level {}\n".format(heatlevel))
				self.__send_feedback_packet(json_dic, STATE_FAIL)
				return

			if (self.miscDeviceHandle.timerinit == 1):
				#
				# when receiving heatfilm's enable command, it begins
				# to start heat timer.
				#
				if (self.miscDeviceHandle.timerenable == 0):
					self.miscDeviceHandle.heat_timer.start()
					self.miscDeviceHandle.timerenable = 1
					p_dbg(DBG_ALERT, "heat timer enable, interval {}\n".format(device_status[ST_TIME][1]))

				if (self.miscDeviceHandle.set_heatfilm(zone, heatlevel) < 0):
					# set fail
					self.__send_feedback_packet(json_dic, STATE_FAIL)
					return
				else:
					# set success
					self.__send_feedback_packet(json_dic, STATE_SUCCESS)
					p_dbg(DBG_DEBUG, "switch on zone {}\n".format(zone))

			else:
				# timer is not init
				self.__send_feedback_packet(json_dic, STATE_FAIL)
				p_dbg(DBG_DEBUG, "heattimer for zone {} is not init\n".format(zone))
		else:
			active_zone = 0
			if (zone == 0):
				pwm.pwm_stop(0) # left heatfilm
				pwm.pwm_stop(1) # right heatfilm
			elif (zone  == 1):
				pwm.pwm_stop(2) # back heatfilm
			elif (zone == 2):
				pwm.pwm_stop(3) # bottom heatfilm

			heatzone_status[zone][2] = False
			p_dbg(DBG_DEBUG, "switch off zone {}\n".format(zone))

			# if all heat zone is disable, it has to cancel heat timer
			for z in range(len(heatzone_status)):
				if (heatzone_status[z][2] == True):
					active_zone = active_zone + 1

			if (active_zone == 0):
				self.miscDeviceHandle.heat_timer.cancel()
				self.miscDeviceHandle.timerinit = 0
				self.miscDeviceHandle.timerenable = 0
				p_dbg(DBG_ALERT, "filmswitch cancel heattimer\n")

			self.__send_feedback_packet(json_dic, STATE_SUCCESS)

		pwm.pwm_dumpAll()

	#
	# parse all UI sented packets and handle them seperately
	#
	def parseMessage(self, request, json_dic):
		p_dbg(DBG_DEBUG, "parseMessage()\n")

		self.reinit_request(request)
		j_id = json_dic["id"]

		# humidity and temperature sensor sample
		if (j_id == PT_SENSOR):
			self.__handle_heartbeattimer()
			self.__handle_sensor(json_dic)

		# heat film's heating level control
		elif (j_id == PT_HEATFILM):
			self.__handle_heatfilm(json_dic)

		# heat period control
		elif (j_id == PT_TIME):
			self.__handle_time(json_dic)

		# lamp etc, switch devices control
		elif (j_id == PT_MISC):
			self.__handle_misc(json_dic)

		# film heat zone switch
		elif (j_id == PT_FILMSWITCH):
			self.__handle_filmswitch(json_dic)

		else:
			p_dbg(DBG_ERROR, "can't parse id: {}".format(json_dic["id"]))

#
# fetch each message from queue and parse it
#
def consume_queue():
	global message_parser
	global message_queue
	p_dbg(DBG_DEBUG, "consume_queue()\n")

	#
	# the below logic is for handling such case:
	# more than one message packets are included in single one network packet.
	# we have to iterate each message packet and parse them.
	#
	q_str = message_queue.get()
	try:
		request = q_str["request"]
		packets_str = q_str["data"]
		#re_match_packets = re.findall('\{.*?\}+', packets_str, re.M|re.I)
		re_match_packets = re_rule.findall(packets_str)
	except:
		p_dbg(DBG_ERROR, "re.findall() error\npacket_str: {}".format(packets_str))
		return

	for i in range(len(re_match_packets)):
		message_dic = json.loads(re_match_packets[i])
		p_dbg(DBG_DEBUG, "re: {}".format(re_match_packets[i]))
		message_parser.parseMessage(request, message_dic)

#
# one specific thread for consuming message queue
# @con: Condition variable
#
def consum_thread(con):
	p_dbg(DBG_DEBUG, "consum_thread()\n")
	while(True):
		if(message_queue.qsize() == 0):
			p_dbg(DBG_INFO, "consumer waiting ...\n")
			con.acquire()
			con.wait()
			con.release()
			p_dbg(DBG_INFO, "consumer run again ...\n")
		else:
			try:
				consume_queue()
			except:
				p_dbg(DBG_ERROR, "consume_queue() fail\n")

#
# get host IP
# @ip_name: eth0
#
def get_ip_address(ip_name):
	sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	ip_addr = socket.inet_ntoa(fcntl.ioctl(sk.fileno(), 0x8915, \
		struct.pack('256s', ip_name[:15]))[20:24])
	return ip_addr

def set_TCPserver(server):
	global g_server
	g_server = server

def get_TCPserver():
	global g_server
	if (g_server):
		return g_server
	else:
		p_dbg(DBG_ERROR, "get_TCPserver g_server is NULL\n")
		return null

#
# a socket server handler class needed by socketserver
#
class SockTCPHandler(socketserver.BaseRequestHandler):

	def handle(self):
		try:
			while (True):
				self.data = self.request.recv(1024)
				p_dbg(DBG_INFO, "{} send: {}\n".format(self.client_address, self.data))
				if (not self.data):
					p_dbg(DBG_ERROR, "connection lost")
					break

				try:
					rcv_data = bytes.decode(self.data)
					j_dic["request"] = self.request
					j_dic["data"] = rcv_data
				except:
					p_dbg(DBG_ERROR, "bytes.decode({}), error\n".format(self.data))
					continue

				con.acquire()
				message_queue.put(j_dic)
				p_dbg(DBG_DEBUG, "queue.put {}".format(j_dic["data"]))
				con.notify()
				con.release()
		except Exception as e:
			p_dbg(DBG_ERROR, "{}, {}".format(self.client_address, "exception error"))
		finally:
			self.request.close()

	def setup(self):
		global message_parser
		if (message_parser == None):
			message_parser = MessageParser(self.request)
			p_dbg(DBG_ALERT, "MessageParser init\n")

		p_dbg(DBG_ALERT, "connect setup() {}\n".format(self.client_address))

	def finish(self):
		server = get_TCPserver()
		server.close_request(self.request)
		p_dbg(DBG_ALERT, "connect finish req {}\n".format(self.client_address))

if __name__ == "__main__":
	verbose = False
	if (len(sys.argv) == 2):
		print(len(sys.argv), sys.argv[1])
		if (sys.argv[1] == "True"):
			verbose = True # output log to stdout for debugging quickly
		else:
			verbose = False # output log to file for debug daemon service
	else:
		print("argv[1] = True: output log to stdout\nargv[1] = False: output log to file")

	p_dbg_init(verbose)

	ip = get_ip_address(str.encode("eth0"))
	HOST,PORT = ip,9998
	p_dbg(DBG_ALERT, "ip: {}, port: {}\n".format(HOST, PORT))
	Thread(target = consum_thread, args = (con,)).start()
	server = socketserver.ThreadingTCPServer((HOST, PORT), SockTCPHandler)
	set_TCPserver(server)
	server.serve_forever()
