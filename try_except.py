#!/usr/bin/python3

import socket
import fcntl
import struct
  
def get_ip_address(inip):
	sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	InIp = socket.inet_ntoa(fcntl.ioctl(sk.fileno(), 0x8915, struct.pack('256s', inip[:15]))[20:24])
	return InIp

print(get_ip_address(str.encode("eth0")))
