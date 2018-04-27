import RPi.GPIO as GPIO
import time
import threading

#GPIO SETUP
channel = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(channel, GPIO.IN)

#IP address: 192.168.0.44
#pi
#chinky@1991

#initialize variables
total_time = 0
start_time = 0
stop_time = 0
user_input = 0

#Thread for looking for user input
def take_input():
    global user_input
    while True:
	user_input = raw_input("")
    return

#timeout function for a 1 minute timer
def timeout():
	global total_time
	global start_time
	global stop_time
	stop_time = time.time() #set stop time as current time
	stop_time = stop_time-10 #account for 1 minute timer before setting stop time
	total_time = total_time + (stop_time - start_time)/3600 #calculate total time in hours
	print "TV time = " + str(total_time)
	#reset start and stop times
	start_time = 0
	stop_time = 0

#callback function for when GPIO pin 17 changes from low to high
def callback(channel):
	global total_time
	global start_time
	global stop_time
	global t
	if GPIO.input(channel): #if high
		if(not start_time): #check if there is already a start time
			start_time = time.time() #set start time to current time
			#create timer thread
			t = threading.Timer(10, timeout)
			t.start() #start 1 minute timer
		else:
			t.cancel() #cancel timer
			t = threading.Timer(10, timeout)
			t.start() #start 1 minute timer
		print "Sound Detected!"
		
		
#detect both rising and falling edges on Pin 17 and call callback on an event
GPIO.add_event_detect(channel, GPIO.RISING, callback = callback, bouncetime = 300)  # let us know when the pin goes HIGH or LOW, 300ms gap between callbacks

#start thread and type "p" to publish to cloud
print('Type p to publish data to cloud')
thread = threading.Thread(target = take_input)
thread.start()

# infinite loop
while True:
	if user_input != 0:
		if user_input == 'p':
			print "Now publishing data"
			print "TV time = " + str(total_time)
		user_input = 0
	else:
		time.sleep(1)
