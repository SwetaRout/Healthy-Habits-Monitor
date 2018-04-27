import glob
import time
from datetime import datetime
import os,json
import ibmiotf.application
import sys

f = open('output.txt','w')
os.system('modprobe w1-gpio') 
os.system('modprobe w1-therm') 
base_dir = '/sys/bus/w1/devices/' 
device_folder = glob.glob(base_dir + '28*')[0] 
device_file = device_folder + '/w1_slave' 
num_of_meals=0 
cook_fl=0 
sum=0 
count=0 
client=None
print "top"
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
      time.sleep(0.2)
      lines = read_temp_raw()
   equals_pos = lines[1].find('t=')
   if equals_pos != -1:
      temp_string = lines[1][equals_pos+2:]
      temp_c = float(temp_string) / 1000.0                 # convert to Celsius
      temp_f = temp_c * 9.0 / 5.0 + 32.0                   # convert to Fahrenheit 
      if(temp_f>130):
	print "COOKING"
	if(cook_fl==0):
		num_of_meals=num_of_meals+1
        cook_fl=1
      else:
	cook_fl=0
	print "NOT COOKING"
      return temp_f

#try:
#	options = {"org":"vwcasz",
#		   "type":"standalone",
#	           "id":"b827eba7",
#	           "auth-method":"use-token-auth",
#                  "auth-token":"f4Q-03@Ti9*gysZdqa",
#		   "auth-key":"a-vwcasz-7ag752fyzc"}
#	client=ibmiotf.application.Client(options)
#	client.connect()
#except ibmiotf.ConnectionException as e:
#	print e


while count<=1000:
   print "here"
   temp_f=read_temp()
   count=count+1
   print count,temp_f,num_of_meals
   time.sleep(1)
   mydata = {'temp':temp_f}
 #  client.publishEvent("RaspberryPi","b827eba7caaf","door","json",mydata)
   time.sleep(0.01)
