# coding=utf-8

import socket
 
HOST = 'localhost'
PORT = 9600
BUFSIZ = 102400
ADDR = (HOST, PORT)

tcpCliSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpCliSock.connect(ADDR)

while True:

	data = raw_input('> ')
	if not data:
		break
		
	tcpCliSock.send("%s\r\n"%data)
	
	data = tcpCliSock.recv(BUFSIZ)
	if not data:
		break
		
	print data.strip()
