#!/usr/bin/python3

import re

#line = "Cats are smarter than dogs"
line = '{"value": 2, "zone": 1, "opcode": 1, "id": 2}{"value": 1, "zone": 2, "opcode": 1, "id": 2}{"value": 3, "zone": 3, "opcode": 1, "id": 2}'

matchObj = re.findall('\{.*?\}+', line, re.M|re.I)
if matchObj:
	print("match --> matchObj.group() : ", matchObj, len(matchObj))
	for i in range(len(matchObj)):
		print(matchObj[i])
		re_dic = eval(matchObj[i])
		print("val = {}, zone = {}, opcode = {}, id = {}".format(re_dic["value"], re_dic["zone"], re_dic["opcode"], re_dic["id"]))
else:
	print("No match!!")
