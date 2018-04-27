from cloudant import Cloudant
from flask import Flask, render_template, request, jsonify
import atexit
import cf_deployment_tracker
import os
import json
import ibmiotf.application
import pandas as pd
import numpy as np
from sklearn import svm
import time
import datetime

client=None
train_dataframe = pd.read_csv('train.csv')
train_labels = train_dataframe.Class_Label
labels = list(set(train_labels))
train_labels = np.array([labels.index(x) for x in train_labels])
train_features = train_dataframe.iloc[:,1:]
train_features = np.array(train_features)

classifier = svm.SVC()
classifier.fit(train_features, train_labels)

count = 0;
results=[]
test_features=[]
test_results=[]

def myCommandCallback(cmd):
	global test_features
	global results
	if cmd.event == "door":
		p=json.loads(cmd.payload)
		num_meals=p['num_of_meals']
		tv=p['tv']
		sleep=p['sleep']
		test_features.append(sleep)
		test_features.append(num_meals)
		test_features.append(tv)		
		print "\n################# temp_f ##################\n"+str(num_meals)
		

# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

# On Bluemix, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8000
port = int(os.getenv('PORT', 8000))

@app.route('/')
def home():
    return render_template('index.html')

# /* Endpoint to greet and add a new visitor to database.
# * Send a POST request to localhost:8000/api/visitors with body
# * {
# *     "name": "Bob"
# * }
# */
@app.route('/api/visitors', methods=['GET'])
def get_visitor():
    print('No database')
    return jsonify([])

# /**
#  * Endpoint to get a JSON array of all the visitors in the database
#  * REST API example:
#  * <code>
#  * GET http://localhost:8000/api/visitors
#  * </code>
#  *
#  * Response:
#  * [ "Bob", "Jane" ]
#  * @return An array of all the visitor names
#  */
@app.route('/api/visitors', methods=['POST'])
def put_visitor():
	if(len(test_features)<3):
		return 'WAITING FOR DATA'
	global classifier
	global test_features
	code=''
	cups = request.json['cups']
	exercise = request.json['exercise']
	cups_val=float(cups)/22;
	exercise_val=float(exercise)/90;
	#results = classifier.predict([[0,exercise_val,cups_val,0,0.8]])
	results = classifier.predict([[float(test_features[-3]),exercise_val,cups_val,float(test_features[-2]),float(test_features[-1])]])
	#val=res*(max-min)+min
	if(len(results)>0):
		for x in results:
			if(x==1):
				code='NOT HEALTHY'
			elif(x==2):
				code='BELOW AVERAGE'
			elif(x==3):
				code='AVERAGE'
			else:
				code='HEALTHY'

	ret = 'Cups of water : '+cups+'<br />'
	ret = ret+'Mins of exercise : '+exercise+'<br />'
	ret = ret+'Number of meals : '+str(float(test_features[-2])*5)+'<br />'
	ret = ret+'Hours of TV : '+str(float(test_features[-1])*5)+'<br />'
	ret = ret+'Hourse of sleep : '+str(float(test_features[-3])*10)+'<br /><br />'
	ret = ret+'You are '+code+'<br />'
	return '%s' %ret

if __name__ == '__main__':
	try:

		options = {"org":"vwcasz","type":"standalone","id":"1","auth-method":"use-token-auth","auth-token":"f4Q-03@Ti9*gysZdqa","auth-key":"a-vwcasz-7ag752fyzc"}
		client=ibmiotf.application.Client(options)
		client.connect()
		client.deviceEventCallback=myCommandCallback
		client.subscribeToDeviceEvents(deviceType="RaspberryPi")

	except ibmiotf.ConnectionException as e:
		print e
	app.run(host='0.0.0.0', port=port, debug=True)
