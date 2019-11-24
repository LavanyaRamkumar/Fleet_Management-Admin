import random, os, json, datetime, time ,string
from flask import *
import hashlib
from pymongo import *
import string 
import datetime
import requests
from flask_cors import *

app = Flask(__name__, static_folder='static')
cors = CORS(app)
client = MongoClient(port=27017)
db = client.FleetManagement
app.secret_key = 'lava'
#client1 = nexmo.Client("key"="your_key", secret="your_secret")

#Admin APIs

@app.route("/bus/route/<rID>/curLoc", methods = ['GET'])    #1
def getCurrentLoc(rID):
  entry = db.PreviousStop.find_one({"routeID":rID})
  prevStopID = entry["prevStopID"]
  entry1 = db.StopSpecifics.find_one({"stopID":prevStopID})
  return entry1["stopname"]

@app.route("/index", methods = ['GET'])    
def ind():
	return (render_template("flee/index.html"))

@app.route("/ts", methods = ['GET'])    
def ts():
	return (render_template("flee/ts.html"))

@app.route("/feedb", methods = ['GET'])    
def feedb():
	return (render_template("flee/feedb.html"))

@app.route("/sms1", methods = ['GET'])    
def sms1():
	return (render_template("flee/sms.html"))


@app.route("/bus/route/curLoc", methods = ['GET']) 
def curLoc():
	#li = ["01PESB2020","02PESB2020"]
	li = ["01PESB2020","02PESB2020","03PESB2020","04PESB2020","05PESB2020","06PESB2020"]
	rou = {}
	for i in li:
		r = requests.get("http://127.0.0.1:8000/bus/route/"+i+"/curLoc")
		rou[i] = r.text
	print(rou)
	return (render_template("flee/cl.html",data = rou))


@app.route("/bus/route/<rID>/students", methods = ['GET'])   #2
def getStudents(rID):
    entries = db.Attendence.find({"routeID":rID})

    students = []
    for i in entries:
      print(i)
      if (i["isBoarded"] == 1):
        students.append(i["userID"])

    obj = jsonify({"u":students})

    return obj
    #return (render_template("trackStudents.html", data = obj))

@app.route("/trackStudents", methods = ['GET']) 
def trackStudents():
	return (render_template("trackStudents.html"))

@app.route("/getFeedback", methods = ['GET']) 
def getFeedback1():
	return (render_template("getFeedback.html"))

#API to check divertion 


@app.route("/bus/route/<rID>/feedback", methods = ['GET'])   #4
def getFeedback(rID):
  """entries = db.DriverDetails.find({"routeID":rID})
  driverID = entries["driverID"]
  print(driverID)"""
  entries1 = db.Feedbacks.find({"routeID":rID});
  feed=[]
  
  for i in entries1:
    j={}
    j["routeID"] = i["routeID"]
    j["nov"] = i["nov"]
    j["description"] = i["description"]
    feed.append(j)
  return jsonify({"u":feed})
 

@app.route("/admin/bus/route/<rID>/emergency", methods = ['POST'])  #5
def postMsgAdmin(rID):
	obj = {}
	obj["from"] = "admin"
	obj["to"] = rID
	j = request.get_json()
	obj["message"] = j["message"]
	obj["fromType"] = "admin"
	obj["timestamp"] = int(time.time())
	db.Emergency.insert(obj);
	return "done"


@app.route("/admin/messages", methods = ['GET'])	#6
def AdminMessages():
	msgs = db.Emergency.find({"to" : "admin"})
	curTime = time.time()
	#print(time.time())
	#obj["timestamp"] = int(time.time()*1000)
	obj = []
	for i in msgs:
		if ((curTime - i["timestamp"]) <= 24*60*60):
			obj.append({"rID":i["from"],"message":i["message"]})
	print(obj)
			
	return (render_template("/flee/mess.html", data = obj))


#API to send SMS from admin to parents and students

@app.route('/Student/getPhoneNumbers', methods = ['POST'])
def return_phonenumbers():
    if request.method!='POST':
      response = app.response_class(response=json.dumps({}), status=405, mimetype='application/json')
      return response      
    content = request.get_json()
    #mycol = mydb["Users"]
    l=content["u"]
    d=[]
    for i in l:
        for x in db.Users.find({} ,{"_id": 0, "userID": 1, "phoneNumber": 1}):  
            if(x["userID"]==i):
              d.append(x["phoneNumber"])
    if(len(d)==0):
      response = app.response_class(response=json.dumps({}), status=400, mimetype='application/json')
      return response    
    return jsonify({"u":d})

 
@app.route('/admin/bus/route/<rID>/sms/<msg>', methods=['GET'])
def send_message(rID,msg):
	r = requests.get("http://127.0.0.1:8000/bus/route/"+rID+"/students")
	#r = r.text
	r = r.text
	print(r)
	#r = json.dumps(r)
	headers = {'content-type': 'application/json'}
	print("huu")
	mob = requests.post("http://127.0.0.1:8000/Student/getPhoneNumbers",data=r,headers=headers)
	#print(mob)
	print(mob.text)
	mob = json.loads(mob.text)
	num = mob["u"]
	num = ",".join(num)
	print(num)
	#num = json.loads(mob.text)
	#print(num)
	#return "done"
	"""j = ",".jsonify(mob)
	print(j)"""

	url = "https://www.fast2sms.com/dev/bulk"
	payload = "sender_id=FSTSMS&message="+msg+"&language=english&route=p&numbers="+num
	#payload = "sender_id=FSTSMS&message=test&language=english&route=p&numbers=9900866772,9480465442"
	headers = {'authorization': "bYEMNI5nKjPhBEZfN4OjD8BUIYmvQQXiiFtP0zkqdjSKfi4INGd6FiEjwfoL",'Content-Type': "application/x-www-form-urlencoded",'Cache-Control': "no-cache", }
	response = requests.request("POST", url, data=payload, headers=headers)
	response = app.response_class(response=json.dumps({}), status=200, mimetype='application/json')
	return response
    


# Driver APIs

@app.route("/bus/route/<rID>", methods = ['GET'])	#8
def getStops(rID):
  route = db.RouteDetails.find({"routeID" : rID})
  stops = route[0]["stopID"]
  entries = db.StopSpecifics.find({"stopID": { "$in": stops} })
  locs=[]
  for i in entries:
    locs.append(i["stopname"])
  return jsonify({"u":locs}) 


@app.route("/bus/route/<rID>/emergency", methods = ['POST'])	#9
def postMsgDriver(rID):
	obj = {}
	obj["from"] = rID
	obj["to"] = "admin"
	j = request.get_json()
	obj["message"] = j["message"]
	obj["fromType"] = "Driver"
	obj["timestamp"] = int(time.time())
	db.Emergency.insert(obj);
	return "done"


@app.route("/bus/route/<rID>/emergency/messages", methods = ['GET'])	#10
def driverMessages(rID):
	msgs = db.Emergency.find({"to" : rID})
	curTime = time.time()
	#print(time.time())
	#obj["timestamp"] = int(time.time()*1000)
	obj = []
	for i in msgs:
		if ((curTime - i["timestamp"]) <= 24*60*60):
			obj.append(i["message"])
			
	return jsonify({"u":obj})


@app.route("/stops/<rID>", methods = ['GET'])	
def stops(rID):
	r = requests.get("http://127.0.0.1:8000/bus/route/"+rID)
	r = json.loads(r.text)
	entries = db.Attendence.find({"routeID": rID})
	uid = []
	for i in entries:
		if(i["IsAbsent"] == 0):
			uid.append(i["userID"])
	print(uid)
	st=[]
	entries1 = db.Stop.find({"userID": { "$in": uid} })
	for i in entries1:
		st.append(i["stopID"])
	entries2 = db.StopSpecifics.find({"stopID": { "$in": st} })
	st2=[]
	for i in entries2:
		st2.append(i["stopname"])
	print(st2)
	final = {}
	for i in r["u"]:
		if i in st2:
			final[i] = 1
		else:
			final[i] = 0

	return (final)



	#return "done"


	



if (__name__ == "__main__"):
  port = int(os.environ.get('PORT', 8000))
  app.run(debug=True, host='0.0.0.0', port=port)
