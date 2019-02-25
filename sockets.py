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

j_dic = {}
con = Condition()
in_q = queue.Queue(10)

class MessagePaser:
	def __init__(self, request):
		self.request = request
		print("init messageparser\n")

	def send_test(self):
		print ("+ send_test ...\n")
		self.request.sendall(str("hello world\n").encode())
		print ("- send_test ...\n")

def consume_queue():
	print("enter consume_queue ...\n")
	while(in_q.empty() != True):
		j_dic_str = in_q.get()
		j_dic = json.loads(j_dic_str)
		print(j_dic)


def consum_thread(con):
	print("enter consum_thread ...\n")
	while(True):
		if(in_q.empty() == True):
			print("consumer waiting ...\n")
			con.acquire()
			con.wait()
			print("consumer run again ...\n")
			con.release()
		else:
			consume_queue()

class MyTCPHandler(socketserver.BaseRequestHandler):

	def handle(self):
		global message_parser
		try:
			while True:
				self.data = self.request.recv(1024)
				print("{} send:".format(self.client_address),self.data)
				if not self.data:
					print("connection lost")
					break

				j_str = bytes.decode(self.data)
				con.acquire()
				in_q.put(j_str)
				con.notify()
				con.release()

				(hum, tem) = hts.ser_get_sensor()
				print(hum, tem)
				ht_str = str('hum: {:.1f}%%RH, tem: {:.1f} \'C'.format(hum, tem))
				print(ht_str)
				#self.request.sendall(str.encode(ht_str))
				message_parser.send_test()
		except Exception as e:
			print(self.client_address,"exception error")
		finally:
			self.request.close()
	def setup(self):
		global message_parser
		message_parser = MessagePaser(self.request)
		print("before handle, setup ...",self.client_address)
	def finish(self):
		print("after handle, finish ...")

if __name__=="__main__":
	HOST,PORT = "localhost",9999
	Thread(target = consum_thread, args = (con,)).start()
	server = socketserver.TCPServer((HOST,PORT), MyTCPHandler)
	server.serve_forever()
	#hts.say_hello()
