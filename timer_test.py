#!/usr/bin/python3

from threading import Timer


def timer1():
	print("timer1()\n")

def timer2():
	global t1
	print("timer2()\n")
	t1.cancel()

if __name__ == "__main__":
	t1 = Timer(10, timer1, ())
	t1.start()
	t = Timer(5, timer2, ())
	t.start()
