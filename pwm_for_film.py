#!/usr/bin/env python3
#
# File name: pwm_for_film.py
# Author: huangq@moxigroup.com
#
# Note: this file implements the PWM control logic for
# heating film.
#
#
#

import wiringpi as wp
import time
from dbg import *

in_out = wp.OUTPUT
low_high = wp.LOW
ENABLE = True

#
# default PWM clock unit: 100us
# period (200 * 100us = 20ms)
# 
#

#
# PWM channels tuble array.
# the channel number is wiringpi coded.
#
channels = (4, 10, 27, 25)

#
# PWM  (wpi - gpio)
# PWM0 (4  - 16)
# PWM1 (10 - 24)
# PWM2 (27 - 36)
# PWM3 (25 - 37)
#
# list[pwm_chl, pin1, pin2, gpio_dir, gpio_level, pwm_period, pwm_dutyon, 'en/dis'able]
#
pwm_parameter = [ \
	[4, 5, 6, 0, 0, 0, 0, False], \
	[10, 11, 26, 0, 0, 0, 0, False], \
	[27, 28, 29, 0, 0, 0, 0, False], \
	[25, 24, 23, 0, 0, 0, 0, False] \
]

def pwm_getParIndex(ch, func):
	if (ch < 0 and ch > 3):
		p_dbg(DBG_ERROR, "{}(): channel {} is invalid.\n".format(func, ch))
		return -1
	else:
		return ch

#
# setup for wiringpi GPIO operation
#
def pwm_wiringPiSetup():
	wp.wiringPiSetup()

#
# initilize one PWM channel to default state
#
def pwm_init(ch, in_out, low_high):
	# config each pin in one PWM channel
	pin1 = pwm_parameter[ch][1]
	pin2 = pwm_parameter[ch][2]
	wp.pinMode(pin1, wp.OUTPUT)
	wp.pinMode(pin2, wp.OUTPUT)
	wp.digitalWrite(pin1, wp.LOW)
	wp.digitalWrite(pin1, wp.HIGH)

	pwm_ch = pwm_parameter[ch][0]
	wp.pinMode(pwm_ch, in_out)
	wp.digitalWrite(pwm_ch, low_high)
	pwm_parameter[ch][3] = in_out
	pwm_parameter[ch][4] = low_high
	p_dbg(DBG_DEBUG, "PWM{}, pin_dir: {}, pin_level: {}, ".format(pwm_ch, in_out, low_high))


#
# set PWM period range
#
def pwm_setPeriod(ch, period):
	pwm_ch = pwm_parameter[ch][0]
	wp.softPwmCreate(pwm_ch, 0, period)
	pwm_parameter[ch][5] = period
	p_dbg(DBG_DEBUG, "period: {}ms ".format(period * 100 / 1000))
	return 0

#
# set PWM duty on time period
#
def pwm_setDuty(ch, duty):
	period = pwm_parameter[ch][5]
	if (period < duty):
		p_dbg(DBG_ERROR, "PWM duty({}) is larger than period({}).\n".format(duty, period))
		return -1
	
	# backup PWM duty-on
	pwm_ch = pwm_parameter[ch][0]
	wp.softPwmWrite(pwm_ch, duty)
	pwm_parameter[ch][6] = duty

	# mark this PWM as 'enable' state
	pwm_parameter[ch][7] = ENABLE
	p_dbg(DBG_DEBUG, "duty: {}ms\n".format(duty * 100 / 1000))
	return 0

#
# config a single PWM channel
# @ch: PWM channel index(0 - 3)
# @in_out: PWM signal pin direction(INPUT, OUTPUT)
# @low_high: PWM signal pin initialized level state
# @period: PWM period range
# @duty: PWM duty on time range
# 
# note: the PWM's clock unit is 100us, @period and @duty parameters
# have to be set based on this 100us unit.
#
def pwm_setSingleChannel(ch, in_out, low_high, period, duty):	
	ch_index = pwm_getParIndex(ch, "pwm_setSingleChannel")
	if (ch_index < 0):
		return ch_index
	else:
		p_dbg(DBG_INFO, "ch_index = {}\n".format(ch_index))

	if (period < duty):
		p_dbg(DBG_ERROR, "PWM duty({}) is larger than period({}).\n".format(duty, period))
		return -2
	
	pwm_init(ch, in_out, low_high)
	pwm_setPeriod(ch, period)
	pwm_setDuty(ch, duty)

	return 0

#
# disable PWM channel
#
def pwm_stop(ch):
	pwm_parameter[ch][7] = not ENABLE
	pwm_ch = pwm_parameter[ch][0]
	wp.softPwmStop(pwm_ch)

#
# dump all PWM channels' configuration
#
def pwm_dumpAll():
	for ch in range(len(channels)):
		if (pwm_parameter[ch][7] == True):
			print("PWM {}: [{}, {}, {}, {}, {}, {}, {}, {}], duty_ratio: {:.1f}%\n".format(ch, \
				pwm_parameter[ch][0], pwm_parameter[ch][1], pwm_parameter[ch][2], \
				pwm_parameter[ch][3], pwm_parameter[ch][4], pwm_parameter[ch][5], \
				pwm_parameter[ch][6], pwm_parameter[ch][7], \
				pwm_parameter[ch][6] * 100 / pwm_parameter[ch][5]))
		else:
			print("PWM {}: [{}, {}, {}, {}, {}, {}, {}, {}]\n".format(ch, \
				pwm_parameter[ch][0], pwm_parameter[ch][1], pwm_parameter[ch][2], \
				pwm_parameter[ch][3], pwm_parameter[ch][4], pwm_parameter[ch][5], \
				pwm_parameter[ch][6], pwm_parameter[ch][7]))

#
# stop all PWM channels
#
def pwm_stopAll():
	p_dbg(DBG_DEBUG, "pwm_stopAll()\n")
	for ch in range(len(channels)):
		if (pwm_parameter[ch][7] == True):
			pwm_stop(ch)

#
# just for PWM channel test
#
def pwm_test():
	pwm_wiringPiSetup()
	while (True):
		ch = input("Input PWM chl(0-3): ")
		if (int(ch) == 4):
			pwm_dumpAll()
			continue

		if (int(ch) == 5):
			pwm_stopAll()
			pwm_dumpAll()
			break

		period = input("Input PWM period(200-1000): ")
		duty = input("Input PWM duty-on(1-period): ")
		pwm_setSingleChannel(int(ch), in_out, low_high, int(period), int(duty))

	print("test done.\n")

if (__name__ == '__main__'):
	pwm_test()
