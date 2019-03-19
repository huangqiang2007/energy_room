# coding=utf-8
 
import SocketServer
import time
 
class WebSocketServer(SocketServer.StreamRequestHandler):
	def handle(self):
		print ("l run")
		print (self.client_address)
		data = self.rfile.readline()
		self.wfile.write('%s %s'%(time.ctime(),data))
		print (data)
		
		# 阻止handle退出 便于分析区别
		while True:
			pass
			
if __name__ == "__main__" :
	# 可以简单将下述ThreadingTCPServer替换为TCPServer
	wsServer = SocketServer.ThreadingTCPServer(( 'localhost',9600),WebSocketServer)
	print ("run")
	wsServer.serve_forever()
