#!/usr/bin/env python3
#
# File name: sockets.py
# Author: huangq@moxigroup.com
#
# Note: this file is the main logic for debugging.
#
#
#
#

#
# debug level enum
#
DBG_ERROR = 0
DBG_ALERT = 1
DBG_INFO  = 2
DBG_DEBUG = 3

def p_dbg(dbglevel, text):
	if (dbglevel <= DBG_DEBUG):
		print(text)
