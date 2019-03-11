#!/usr/bin/python3 

import socket # 导入 socket 模块

s = socket.socket() # 创建 socket 对象
host = socket.gethostname() # 获取本地主机名
port = 1028 # 设置端口好

s.connect(('192.168.1.206', port))
print (s.recv(1024).decode())
s.close()
