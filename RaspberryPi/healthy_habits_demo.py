import glob
import time
from datetime import datetime
import os,json
import ibmiotf.application
import sys
import RPi.GPIO as GPIO
import threading
import serial
from time import strftime, sleep
from threading import Timer

#GPIO SETUP for sound sensor
channel = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(channel, GPIO.IN)

#f = open('output.txt','w')
#sys.stdout=f
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'
num_of_meals=0
cook_fl=0
sum=0
#initialize sound variables
total_time = 0
start_time = 0
stop_time = 0
user_input = 0
client=None
#initialize sleeping variables
filterReady = False
avg = 0
sleep_sum = 0
sampleCount = 0
onBedThreshold = 200
onTheBedFlag = False
maxSleep = 12 #in minutes - 12 hours
minSleep = 4 #in minutes - 4 hours
normalizedSleep = 0
accumulatedSleep = 0 #in minutes

#Thread for looking for user input
def take_input():
    global user_input
    while True:
	user_input = raw_input("")
    return

def feed(val):
   global filterReady
   global avg
   global sleep_sum
   global sampleCount
   windowSize = 5

   if(sampleCount < windowSize):
      sleep_sum += val
      sampleCount += 1
      if sampleCount == windowSize:
         avg = sleep_sum/windowSize
         filterReady = True
   else:
      avg = sleep_sum/windowSize
      sleep_sum -= avg
      sleep_sum += val

def stopWatch(value):
    global accumulatedSleep
    '''From seconds to Days;Hours:Minutes;Seconds'''
    seconds = int(value)
    accumulatedSleep += float(seconds/60)
    print(accumulatedSleep)

def publishSleepInADay():
	global accumulatedSleep
	global normalizedSleep

	normalizedSleep = (float(accumulatedSleep) - minSleep) / (maxSleep - minSleep)
	print(normalizedSleep)
	accumulatedSleep = 0
	
#timeout function for a 1 minute timer
def timeout():
	global total_time
	global start_time
	global stop_time
	stop_time = time.time() #set stop time as current time
	stop_time = stop_time-10 #account for 1 minute timer before setting stop time
	total_time = total_time + (stop_time - start_time)/60 #calculate total time in hours
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

def read_temp_raw():
        f = open(device_file, 'r')
        lines = f.readlines()
        return lines

def read_temp():
   global num_of_meals
   global cook_fl
   prev_time = time.time()
   hours=0
   lines = read_temp_raw()
   while lines[0].strip()[-3:] != 'YES':
      #time.sleep(0.2)
      lines = read_temp_raw()
   equals_pos = lines[1].find('t=')
   if equals_pos != -1:
      temp_string = lines[1][equals_pos+2:]
      temp_c = float(temp_string) / 1000.0                 # convert to Celsius
      temp_f = temp_c * 9.0 / 5.0 + 32.0                   # convert to Fahrenheit
      if(temp_f>105):
        print "COOKING"
        if(cook_fl==0):
		print "start cooking",num_of_meals
                num_of_meals=num_of_meals+1
        cook_fl=1
      else:
        cook_fl=0
        print temp_f
      return temp_f,num_of_meals

ser=serial.Serial("/dev/ttyACM0",9600)  #setup communication to Arduino
ser.baudrate=9600
force = 0
	  
print ("before")
try:
	options = {"org":"vwcasz",
			   "type":"standalone",
			   "id":"b827eba7",
			   "auth-method":"use-token-auth",
			   "auth-token":"f4Q-03@Ti9*gysZdqa",
			   "auth-key":"a-vwcasz-7ag752fyzc"}
	client=ibmiotf.application.Client(options)
	client.connect()
	print "connected"
except ibmiotf.ConnectionException as e:
	print e

#detect both rising and falling edges on Pin 17 and call callback on an event
print "here"
GPIO.add_event_detect(channel, GPIO.RISING, callback = callback, bouncetime = 300)  # let us know when the pin goes HIGH or LOW, 300ms gap between callbacks

#start thread and type "p" to publish to cloud
print('Type p to publish data to cloud')
thread = threading.Thread(target = take_input)
thread.start()
		
while True:
	if user_input != 0:
		if user_input == 'p':
			print "Now publishing data"
			print "TV time = " + str(float(total_time)/5)
			print "Number of meals = " +str(float(num_of_meals)/5)
			publishSleepInADay
			print "Hours slept = " +str(normalizedSleep)
			mydata = {'num_of_meals':str(float(num_of_meals)/5),'tv':str(float(total_time)/5),'sleep':str(normalizedSleep)}
			client.publishEvent("RaspberryPi","b827eba7caaf","door","json",mydata)
		user_input = 0
	else:
		if ser.inWaiting() > 0:
			read_ser=ser.readline().strip('\0')
			try:
				force = int(read_ser)
				print force
			except ValueError:
				pass

			if type(force) == int:
				feed(force)

		if filterReady == True:
			#sleep(0.5)
			#print avg
			if avg > onBedThreshold:
				if onTheBedFlag == False:
					onTheBedFlag = True
					start = time.time()
					print("on the bed")
			else:
				if onTheBedFlag == True:
					onTheBedFlag = False
					end = time.time()
					stopWatch(end-start)
					print("off the bed")
			   
		temp_f,num_of_meals=read_temp()
		print temp_f,num_of_meals
		#client.publishEvent("RaspberryPi","b827eba7caaf","door","json",mydata)
		#time.sleep(0.01)
