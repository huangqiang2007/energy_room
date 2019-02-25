#!/usr/bin/env python3

from threading import Condition, Thread
import socketserver
import queue
import json

j_dic = {}
con = Condition()
q = queue.Queue(10)

def consume_queue():
	print("enter consume_queue ...\n")
	while(q.empty() != True):
		j_dic_str = q.get()
		j_dic = json.loads(j_dic_str)
		print(j_dic)


def consum_thread(con):
	print("enter consum_thread ...\n")
	while(True):
		if(q.empty() == True):
			print("consumer waiting ...\n")
			con.acquire()
			con.wait()
			print("consumer run again ...\n")
			con.release()
		else:
			consume_queue()

class MyTCPHandler(socketserver.BaseRequestHandler):
	def handle(self):
		try:
			while True:
				self.data = self.request.recv(1024)
				print("{} send:".format(self.client_address),self.data)
				if not self.data:
					print("connection lost")
					break

				j_str = bytes.decode(self.data)
				con.acquire()
				q.put(j_str)
				con.notify()
				con.release()
				self.request.sendall(self.data)
		except Exception as e:
			print(self.client_address,"exception error")
		finally:
			self.request.close()
	def setup(self):
		print("before handle, setup ...",self.client_address)
	def finish(self):
		print("after handle, finish ...")

if __name__=="__main__":
	HOST,PORT = "localhost",9999
	Thread(target = consum_thread, args = (con,)).start()
	server = socketserver.TCPServer((HOST,PORT), MyTCPHandler)
	server.serve_forever()
