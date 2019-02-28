#!/usr/bin/env python3
#
# File name: gpio_test.py
# Author: huangq@moxigroup.com
#
# Note: this file is used for raspberry GPIO test according to
# wiringpi define framework.
#
#
#

import wiringpi as wp
import time
from dbg import *

#
# PWM  (wpi - gpio)
# PWM0 (4  - 16)
# PWM1 (10 - 24)
# PWM2 (27 - 36)
# PWM3 (25 - 37)
#

low_level = 0

wp.wiringPiSetup()

#
# default PWM clock unit: 100us
# period (200 * 100us = 20ms)
# 
#

#
# PWM channels tuble array.
# the channel number is wiringpi coded.
#
ch_arr = (4, 10, 27, 25)

pwm_pars_list = [ \
	[4, 1, 0, 200, 100], \
	[10, 1, 0, 200, 100], \
	[27, 1, 0, 200, 100], \
	[25, 1, 0, 200, 100] ]

def pwm_getParIndex(ch, func):
	if (ch < 0 and ch > 3):
		p_dbg(DBG_ERROR, "{}(): channel {} is invalid.\n".format(func, ch))
		return -1
	else:
		return ch

#
# initilize one PWM channel to default state
#
def pwm_init(ch, in_out, low_high):
	# backup pin direction and level
	pwm_ch = pwm_pars_list[ch][0]
	pwm_pars_list[ch][1] = in_out
	pwm_pars_list[ch][2] = low_high

	wp.pinMode(pwm_ch, in_out)
	wp.digitalWrite(pwm_ch, low_high)
	p_dbg(DBG_DEBUG, "PWM{}, pin_dir: {}, pin_level: {}, ".format(pwm_ch, in_out, low_high))


#
# set PWM period range
#
def pwm_setPeriod(ch, period):
	pwm_ch = pwm_pars_list[ch][0]
	wp.softPwmCreate(pwm_ch, 0, period)
	p_dbg(DBG_DEBUG, "period: {}ms ".format(period * 100 / 1000))
	return 0

#
# set PWM duty on time period
#
def pwm_setDuty(ch, duty):
	period = pwm_pars_list[ch][3]	
	if (period < duty):
		p_dbg(DBG_ERROR, "PWM duty({}) is larger than period({}).\n".format(duty, period))
		return -1
	
	# backup PWM duty-on
	pwm_ch = pwm_pars_list[ch][0]
	wp.softPwmWrite(pwm_ch, duty)
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
	pwm_ch = pwm_pars_list[ch][0]
	wp.softPwmStop(pwm_ch)


while (True):
	ch = input("Input PWM chl(0-3): ")
	if (int(ch) > 3):
		pwm_stop(old_ch)
		print("PWM{} exit\n".format(old_ch))
		break

	old_ch = int(ch)
	period = input("Input PWM period(200-1000): ")
	duty = input("Input PWM duty-on(1-period): ")
	pwm_setSingleChannel(int(ch), wp.OUTPUT, low_level, int(period), int(duty))

print("test done.\n")


#while (True):
#	inpt = wp.digitalRead(PWM_CH)
#	print("GPIO{} state {}\n".format(PWM_CH, inpt))
#	time.sleep(5)
#	low_level = not low_level
#	wp.digitalWrite(PWM_CH, low_level)
