#!/bin/sh

while [ 1 ]
do
	#echo "hello world!"
	sleep 1
done

#python3 hello.py
if [ $? -ne 0 ];then
	echo "\nrun hello.py error"
	exit 1
else
	echo "\nrun hello.py ok"
#python3 world.py        
fi

echo "test done!"
