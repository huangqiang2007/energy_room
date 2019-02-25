#!/usr/bin/python3

import socket
import json

j_dic = {}

client=socket.socket()
client.connect(('localhost',9999))

while True:
	jid=input("\nid> ")
	if len(jid)==0:
		continue
	if jid == "quit":
		break
	jtype = input("type> ")
	jvalue = input("value> ")
	j_dic["id"] = int(jid)
	j_dic["type"] = int(jtype)
	j_dic["value"] = int(jvalue)
	j_dic_str = json.dumps(j_dic)
	j_dic_bytes = str.encode(j_dic_str)
#	print(j_dic_bytes)
	client.send(j_dic_bytes)
	dic_res=client.recv(1024)
	print(dic_res.decode())

client.close()
