#-*- coding:utf-8 -*-
from detect_simple import detect
from PIL import Image
import paho.mqtt.client as mqtt
import cv2
import argparse
import time
import threading
import queue
import datetime as dt
from pprint import pprint
import json
import re

import boto3
from botocore.exceptions import ClientError
import os 

# IAM ID, Key Setting
my_id = ''
my_key = ''

q = queue.Queue()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("connected OK")
    else:
        print("Bad connection Returned code=", rc)


def on_disconnect(client, userdata, flags, rc=0):
    print(str(rc))


def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed: " + str(mid) + " " + str(granted_qos))


# detect parking
def on_message(client, userdata, msg):
    message = str(msg.payload.decode("utf-8")).split('-')
    camera, location, In_out = message
    #print(f"{camera}-{location}-{In_out}")
    # B1/B2 - A1 A2 A3 - In/out
    print()
    print("=============================")
    print(f"detect 감지 : {camera} - {location} - {In_out}")
    print("=============================")
    print()
    info = {"parkingLotIndex" : 1, "section" : camera, "type": In_out, "createdAt": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    q.put((location, info))
    
    
# 카메라 스냅샷    
def detect_Snapshot(camera):
  if camera == "B1":
    url = 'rtsp://id:password@192.168.0.23/'
  elif camera == "B2":
    url = 'rtsp://id:password@192.168.0.23/' # 24로 바꾸기

  cap = cv2.VideoCapture(url)

  ret, image = cap.read()

  if not ret:
    print("Snapshot Error!")
    return
  # 후에 없앨 것
  if camera == "B1":
    cv2.imwrite('./camera/camera1.jpg', image)
    img_path = './camera/camera1.jpg'
  elif camera == "B2":
    cv2.imwrite('./camera/camera2.jpg', image)
    img_path = './camera/camera2.jpg'

  return img_path


def start(location, info):
    camera = info["section"]
    In_out = info["type"]
    jdict = dict()

    #img_path = detect_Snapshot(camera)
    img_path = './camera/camera1.jpg'
    jdict["info"] = info
    if location != "snapshot":
        info["type"] = "parking"
        if In_out == "In":
            data = detect(img_path, location)
            data = data[int(location[-1])-1]
        elif In_out == "Out":
            data = {"location": location, "inOut": "out"}
        
        jdict["data"] = [data]

        return jdict
    
    data = detect(img_path, location)
    jdict["data"] = data
    return jdict 

def subscribing():
    client.on_message = on_message
    client.loop_forever()


def Timesnap():
    print()
    print("=============================")
    print("SNAPSHOT")
    print("=============================")
    print()
    # B1 B2 둘다 넣기
    info = {"parkingLotIndex" : 1, "section" : "B1", "type": "snapshot", "createdAt": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    q.put(("snapshot",info))
    info = {"parkingLotIndex" : 1, "section" : "B2", "type": "snapshot", "createdAt": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    q.put(("snapshot",info))
    threading.Timer(180, Timesnap).start()


def event_queue():
    while True:
        location, info = q.get()
        print()
        print("=============================")
        print(f"detect start : {location}")
        print("=============================")
        jdict = start(location, info) # snapshot A1 A2 A3
        saved_json_image(jdict)
        print("=============================")
        print(f"detect {location} end")
        print("=============================")
        print()

        q.task_done()


s3 = boto3.client(
    's3',  # s3 service
    aws_access_key_id=my_id,         # Access ID
    aws_secret_access_key=my_key)    # Secret Access Key


def create_s3_bucket(bucket_name):
    print("Creating a bucket... " + bucket_name)

    try:
        response = s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': 'ap-northeast-2' # Seoul Region
            }
        )
        return response
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou': # If already have bucket
            print("Bucket already exists. skipping..")
        else:
            print("Unknown error, exit..")   

def saved_json_image(jdict):
  response = create_s3_bucket("parking-management-s3") # Bucket Name Setting
  print("Bucket : " + str(response))
  files = []
  stored_names = []
  section = jdict['info']['section'][-1]
  for i in range(len(jdict['data'])):
    if jdict['data'][i]['inOut'] == 'in':
      loc = jdict['data'][i]['location'][-1]
      files.append(f'./detections/crop/camera{section}/license_plate_{loc}.jpg')
      numbers = re.sub(r'[^0-9]', '', jdict['info']['createdAt'])
      img_Url = f"carImg/{numbers}_A{loc}.jpg"
      json_Url = f"carData/{numbers}.json"
      jdict['data'][i]['imgUrl'] = img_Url
      stored_names.append(img_Url)
  pprint(jdict)
  for file, stored_name in zip(files, stored_names):
      print(file, stored_name)
      s3.upload_file(file, "parking-management-s3", stored_name)
  with open("./result/data.json", "w") as f:
    json.dump(jdict, f)
  s3.upload_file("./result/data.json", "parking-management-s3", json_Url)

if __name__ == '__main__':
    
    '''
    client = mqtt.Client()
    # 콜백 함수 설정 on_connect(브로커에 접속), on_disconnect(브로커에 접속중료), on_subscribe(topic 구독),
    # on_message(발행된 메세지가 들어왔을 때)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe
    # address : localhost, port: 1883 에 연결
    client.connect('192.168.0.33', 1883)
    # common topic 으로 메세지 발행
    client.subscribe('test', 1)
    
    sub = threading.Thread(target = subscribing)
    event_queue = threading.Thread(target=event_queue, daemon=True)
    sub.start()
    Timesnap()
    event_queue.start()
    '''
    
    info = {"parkingLotIndex" : 1, "section" : "B1", "type": "In", "createdAt": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    jdict = start("A1",info)
    saved_json_image(jdict)