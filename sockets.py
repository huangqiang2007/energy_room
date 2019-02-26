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
from threading import Condition, Thread
import socketserver
import queue
import json
#from hum_tem_sensor import *
import hum_tem_sensor as hts
from dbg import *

j_dic = {}
con = Condition()
in_q = queue.Queue(10)

#
# event packet type
#
EV_SENSOR = 1
EV_HEATFILM = 2
EV_LIGHT = 3
EV_HUMDIFIER = 4
EV_BLUE_SPEAKER = 5


#
# this class is responsible for parse all packets
# which come from client(UI input)
#
class MessagePaser:
	def __init__(self, request):
		self.request = request
		p_dbg(DBG_INFO, "init messageparser\n")

	def send_test(self):
		print ("+ send_test ...\n")
		self.request.sendall(str("hello world\n").encode())
		print ("- send_test ...\n")

	def __handle_sensor(self, json_dic):
		(hum, tem) = hts.ser_get_sensor()
		json_dic["hum"] = hum
		json_dic["tem"] = tem
		p_dbg(DBG_DEBUG, "id = {:d}, type = {:d}, value = {:d}, hum = {:.1f}, tem = {:.1f}\n".format(json_dic["id"], json_dic["type"], json_dic["value"], json_dic["hum"], json_dic["tem"]))
		self.request.sendall(str.encode(json.dumps(json_dic)))

	def __handle_light(self, json_dic):
		p_dbg(DBG_DEBUG, "msg id: {}\n".format(json_dic["id"]))
		self.request.sendall(str.encode("__handle_light()\n"))

	def __handle_heatfilm(self, json_dic):
		p_dbg(DBG_DEBUG, "msg id: {}\n".format(json_dic["id"]))
		self.request.sendall(str.encode("__handle_heatfilm()\n"))

	def __handle_humdifier(self, json_dic):
		p_dbg(DBG_DEBUG, "msg id: {}\n".format(json_dic["id"]))
		self.request.sendall(str.encode("__handle_humdifier()\n"))

	def __handle_blue_speaker(self, json_dic):
		p_dbg(DBG_DEBUG, "msg id: {}\n".format(json_dic["id"]))
		self.request.sendall(str.encode("__handle_blue_speaker()\n"))


	def parseMessage(self, json_dic):
		p_dbg(DBG_DEBUG, "parseMessage()\n")
		j_id = json_dic["id"]
		if (j_id == EV_SENSOR):
			self.__handle_sensor(json_dic)

		elif (j_id == EV_HEATFILM):
			self.__handle_heatfilm(json_dic)

		elif (j_id == EV_LIGHT):
			self.__handle_light(json_dic)

		elif (j_id == EV_HUMDIFIER):
			self.__handle_humdifier(json_dic)

		elif (j_id == EV_BLUE_SPEAKER):
			self.__handle_blue_speaker(json_dic)

		else:
			self.request.sendall(str.encode("can't parse id: {}".format(json_dic["id"])))


def consume_queue():
	global message_parser
	p_dbg(DBG_DEBUG, "consume_queue()\n")
	j_dic_str = in_q.get()
	j_dic = json.loads(j_dic_str)
	message_parser.parseMessage(j_dic)


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
		message_parser = MessagePaser(self.request)
		p_dbg(DBG_ALERT, "connect setup() {}\n".format(self.client_address))
	def finish(self):
		p_dbg(DBG_ALERT, "connect finish()\n")

if __name__ == "__main__":
	HOST,PORT = "localhost",9999
	Thread(target = consum_thread, args = (con,)).start()
	server = socketserver.TCPServer((HOST,PORT), SockTCPHandler)
	server.serve_forever()
