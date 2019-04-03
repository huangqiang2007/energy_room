#!/usr/bin/env python3
#
# File name: misc_dev.py
# Author: huangq@moxigroup.com
#
# Note: this file implements the logic for control
# misc device.
#
#
#


import wiringpi as wp
import time
from dbg import *

#
# the GPIO control pin for all switch devices, the number is given
# according to wiringpi rule.
#
# wiringpi GPIO
# 7			7
# 0			11
# 2			13
# 3			15
# 12		19
# 13		21
# 14		23
#
GPIO_LAMP = 13
GPIO_RDLIGHT = 14
GPIO_WET = 12
GPIO_FAN = 3
GPIO_OB = 2
GPIO_AU = 0
GPIO_AH = 7

#
# status record table for all switch channels
# [gpio, state]
#
misc_dev_status = [
	[GPIO_LAMP, False],
	[GPIO_RDLIGHT, False],
	[GPIO_WET, False],
	[GPIO_FAN, False],
	[GPIO_OB, False],
	[GPIO_AU, False],
	[GPIO_AH, False],
]

g_misc_wiringpisetup_flag = False

#
# setup for wiringpi GPIO operation
#
def misc_wiringPiSetup():
	global g_misc_wiringpisetup_flag
	if (g_misc_wiringpisetup_flag == False):
		wp.wiringPiSetup()
		g_misc_wiringpisetup_flag = True

def misc_init():
	p_dbg(DBG_DEBUG, "misc_init()\n")
	misc_wiringPiSetup()
	for i in range(len(misc_dev_status)):
		pin = misc_dev_status[i][0]
		#wp.pullUpDnControl(pin, wp.PUD_OFF)
		wp.pinMode(pin, wp.OUTPUT)
		wp.digitalWrite(pin, wp.LOW)

def misc_configSingleDev(index, state):
	p_dbg(DBG_DEBUG, "misc_configSingleDev()\n")
	ret = 0
	ch_idx = index - 1
	if (ch_idx < 0 or ch_idx > 6):
		p_dbg(DBG_ERROR, "misc_configSingleDev() ch_idx {} beyond\n".format(ch_idx))
		return -1

	pin = misc_dev_status[ch_idx][0]
	if (state == 0):
		wp.digitalWrite(pin, wp.LOW)
		misc_dev_status[ch_idx][1] = False
	elif (state == 1):
		wp.digitalWrite(pin, wp.HIGH)
		misc_dev_status[ch_idx][1] = True
	else:
		p_dbg(DBG_ALERT, "misc_configSingleDev() state {} invalid\n".format(state))
		return -1

	p_dbg(DBG_INFO, "misc_configSingleDev({}-{}, {})\n".format(index, pin, state))
	return ret


