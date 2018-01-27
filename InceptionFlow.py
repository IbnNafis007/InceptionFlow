# *****************************************************************************
# InceptionFlow
# Copyright (c) 2018 Adam Milton-Barker - AdamMiltonBarker.com
# Based on Google's Tensorflow Imagenet Inception V3
# Uses TechBubble IoT JumpWay MQTT Client
# *****************************************************************************

import sys
import os
import time
import json

from datetime import datetime

import techbubbleiotjumpwaymqtt.device as IoTJumpWayDevice
import techbubbleiotjumpwaymqtt.application as IoTJumpWayApplication
import InceptionFlow
import cv2

class InceptionFlowCore():
    	
	def __init__(self):
    		
		#self.Mode =""
		self.Mode = "ObjectLocal"
		#self.Mode = "ObjectCam"
		#self.Mode = "FacialLocal"
		#self.Mode = "FacialCam"

		self.Train=False
		self.Test=True
    		
		self.confs = {}
		self.threshold = 0.75

		self.InceptionFlow = InceptionFlow.InceptionFlow()
		
		with open('data/confs.json') as confs:
			
			self.confs = json.loads(confs.read())
			
		self.startMQTT()
		self.InceptionFlow.checkModelDownload()
		self.InceptionFlow.createGraph()
		
		if self.Mode == "ObjectLocal":
        
			try:
    			
				self.OpenCVCapture = cv2.VideoCapture(0)

			except Exception as e:
				print("FAILED TO CONNECT TO WEBCAM")
				print(str(e))
				sys.exit()
		
		elif self.Mode == "FacialLocal":
        
			try:
    			
				self.OpenCVCapture = cv2.VideoCapture(0)

			except Exception as e:
				print("FAILED TO CONNECT TO WEBCAM")
				print(str(e))
				sys.exit()
		
	def startMQTT(self):
        
		try:

			self.JumpWayMQTTClient = IoTJumpWayApplication.JumpWayPythonMQTTApplicationConnection({
				"locationID": self.confs["IoTJumpWaySettings"]["SystemLocation"],
				"applicationID": self.confs["IoTJumpWaySettings"]["SystemApplicationID"],
				"applicationName": self.confs["IoTJumpWaySettings"]["SystemApplicationName"],
				"username": self.confs["IoTJumpWayMQTTSettings"]["MQTTUsername"],
				"password": self.confs["IoTJumpWayMQTTSettings"]["MQTTPassword"]
			})

		except Exception as e:
			print(str(e))
			sys.exit()

		self.JumpWayMQTTClient.connectToApplication()
		
	def objectTesting(self):
		
		print("TESTING OBJECTS")
		print("")
		rootdir=os.getcwd()+"/model/testing/Objects/"
		
		for file in os.listdir(rootdir):

			if file.endswith(".jpg"): 

				print("FILE: "+file)

				fileName = rootdir+"/"+file
				label,confidence = self.InceptionFlow.classifyObject(fileName)
				
				if label:
					
					print("IMAGE: "+file)
					print("OBJECT: "+str(label))
					print("Confidence: "+str(confidence))
					print("")

		print("")
		print("COMPLETING TESTING OBJECTS")
		
InceptionFlowCore = InceptionFlowCore()

while True:
    	
	if InceptionFlowCore.Train==True:
    		
		pass
    		
	elif InceptionFlowCore.Test==True:
    		
		if InceptionFlowCore.Mode == "ObjectCam" or InceptionFlowCore.Mode == "ObjectLocal":	
		
			InceptionFlowCore.objectTesting()
			#InceptionFlowCore.Test=False
			
			print("TESTING DEACTIVATED")
    		
	else:
		
		if InceptionFlowCore.Mode == "ObjectLocal":	
    	
			try:
				
				ret, frame = InceptionFlowCore.OpenCVCapture.read()
				if not ret: continue

				savedFrame = InceptionFlowCore.InceptionFlow.saveImage(frame)
				Object,Confidence = InceptionFlowCore.InceptionFlow.classifyObject(savedFrame)
				
				if Object and Confidence > InceptionFlowCore.threshold:
						
					print("Object: "+str(Object))
					print("Confidence: "+str(Confidence))
					
					InceptionFlowCore.JumpWayMQTTClient.publishToDeviceChannel(
							"Sensors",
							InceptionFlowCore.confs["IoTJumpWaySettings"]["SystemZone"],
							InceptionFlowCore.confs["IoTJumpWaySettings"]["SystemDeviceID"],
							{
								"Sensor":"CCTV",
								"SensorID": InceptionFlowCore.confs["Cameras"][0]["ID"],
								"SensorValue":"OBJECT: " + str(Object) + " (Confidence: " + str(Confidence) + ")"
							}
						)

				time.sleep(1)
			
			except cv2.error as e:
				print(e)       

InceptionFlowCore.OpenCVCapture.release()
cv2.destroyAllWindows()
InceptionFlowCore.JumpWayMQTTClient.disconnectFromApplication()
