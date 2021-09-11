#-*- coding:utf-8 -*-
from detect_simple import detect
from PIL import Image
import paho.mqtt.client as mqtt
import cv2
import argparse
import time
import threading
import queue
 
 
q = queue.Queue()
i = 0
 
def on_connect(client, userdata, flags, rc):
   if rc == 0:
       print("connected OK")
   else:
       print("Bad connection Returned code=", rc)
 
 
def on_disconnect(client, userdata, flags, rc=0):
   print(str(rc))
 
 
def on_subscribe(client, userdata, mid, granted_qos):
   print("subscribed: " + str(mid) + " " + str(granted_qos))
 
 
def on_message(client, userdata, msg):
   message = str(msg.payload.decode("utf-8")).split('-')
   camera, location, In_out = message
   global i
   #print(f"{camera}-{location}-{In_out}")
   print("=============================")
   print("q에 detect 넣기 : ", i)
   print("=============================")
   print()
   q.put(("detected", i))
   i += 1
   return location, In_out
  
  
def detect_Snapshot(loc):
 url = 'rtsp://ID:password@Ip/'
 cap = cv2.VideoCapture(url)
 
 ret, image = cap.read()
 
 if not ret:
   print("Snapshot Error!")
   return
 # 후에 없앨 것
 if loc == "B1":
   cv2.imwrite('./camera/camera1.jpg', image)
   img_path = './camera/camera1.jpg'
 elif loc == "B2":
   cv2.imwrite('./camera/camera2.jpg', image)
   img_path = './camera/camera2.jpg'
 
 return img_path
 
 
def start(location, In_out):
   detect_Snapshot(1)
   #Snapshot(2)
   img_path = ['camera1.jpg','camera2.jpg']
   detect(img_path)
  
 
def subscribing():
   client.on_message = on_message
   client.loop_forever()
 
 
def Timesnap():
   #print("Hello!")
   # queue 넣어주기
   global i
   print("=============================")
   print("q에 snapshot 넣기 :", i)
   print("=============================")
   print()
   q.put(("snapshot",i))
   i += 1
   threading.Timer(10, Timesnap).start()
 
 
def event_queue():
   while True:
       item, num = q.get()
       print(f"------detect start : {num} - {item}------")
       time.sleep(20)
       print(f"--------------detect {num} end-----------")
       print()
 
       q.task_done()
 
 
if __name__ == '__main__':
  
   client = mqtt.Client()
   # 콜백 함수 설정 on_connect(브로커에 접속), on_disconnect(브로커에 접속중료), on_subscribe(topic 구독),
   # on_message(발행된 메세지가 들어왔을 때)
   client.on_connect = on_connect
   client.on_disconnect = on_disconnect
   client.on_subscribe = on_subscribe
   # address : localhost, port: 1883 에 연결
   client.connect('Ip', "port")
   # common topic 으로 메세지 발행
   client.subscribe('test', 1)
  
   sub = threading.Thread(target = subscribing)
   event_queue = threading.Thread(target=event_queue, daemon=True)
   sub.start()
   Timesnap()
   event_queue.start()