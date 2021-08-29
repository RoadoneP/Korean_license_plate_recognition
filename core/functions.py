import os
import cv2
import random
import numpy as np
import tensorflow as tf
import datetime as dt

from core.utils import read_class_names
from core.config import cfg
from time import time

from ocr.model import LPRNet
from ocr.loader import resize_and_normailze



# function for cropping each detection and saving as new image
def crop_objects(img, data, path, allowed_classes):
    boxes, scores, classes, num_objects = data
    class_names = read_class_names(cfg.YOLO.CLASSES)
    #create dictionary to hold count of objects for image name
    jdict = dict()
    counts = dict()
    for i in range(num_objects):
        # get count of class for part of image name
        class_index = int(classes[i])
        class_name = class_names[class_index]
        if class_name in allowed_classes:
            counts[class_name] = counts.get(class_name, 0) + 1
            # get box coords
            xmin, ymin, xmax, ymax = boxes[i]
            is_electric_car = electric_car(img, boxes[i])
            location = loc(img, xmin, xmax)
            #print(location)
            # crop detection from image (take an additional 5 pixels around all edges)
            cropped_img = img[int(ymin)-3:int(ymax)+3, int(xmin)-3:int(xmax)+3]
            # construct image name and join it to path for saving crop properly
            img_name = class_name + '_' + str(counts[class_name]) + '.jpg'
            img_path = os.path.join(path, img_name)
            # save image
            cv2.imwrite(img_path, cropped_img)
            carNum = OCR(img_path)
            count = {"carNum" : carNum, "classify" : is_electric_car, "location" : location, "time" : dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "credit" : scores[i], "inOut": True }   
        else:
            continue
        
        jdict[i] = count
        
    return jdict
        
classnames = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
              "가", "나", "다", "라", "마", "거", "너", "더", "러",
              "머", "버", "서", "어", "저", "고", "노", "도", "로",
              "모", "보", "소", "오", "조", "구", "누", "두", "루",
              "무", "부", "수", "우", "주", "허", "하", "호"
              ]

def OCR(img):
    t = time()
    args = {'image' : img, 'weights' : './ocr/weights_best.pb'}

    #tf.compat.v1.enable_eager_execution()
    net = LPRNet(len(classnames) + 1)
    net.load_weights(args["weights"])

    img = cv2.imread(args["image"])
    #img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    x = np.expand_dims(resize_and_normailze(img), axis=0)
    
    carNum = net.predict(x, classnames)
    #print(carNum)
    print('ocr: ',time() - t)
    #cv2.imshow("lp", img)
    #cv2.waitKey(0)
    cv2.destroyAllWindows()
    return carNum

def loc(image, xmin, xmax):
  image_h, image_w, _ = image.shape
  xmin = xmin/image_w
  xmax = xmax/image_w
  center = (xmin + xmax) / 2
 
  if center>=0 and center < 0.33:
    loc = "A1"
  elif center>=0.33 and center< 0.66:
    loc = "A2"
  else:
    loc = "A3"

  return loc

def electric_car(image, bbox):
  xmin, ymin, xmax, ymax = bbox
  elec_plate = image[int(ymin):int(ymax),int(xmin):int(xmax)]
  elec_plate = cv2.cvtColor(elec_plate, cv2.COLOR_BGR2RGB)
  #cv2.imshow("lp",elec_plate)
  #cv2.waitKey(0)
  isElectronic = 0 
  notElectronic = 0
  elec_range = elec_plate.copy()

  Y, X, _ = elec_range.shape
  
  for y in range(Y):
    for x in range(X):
        # 조건 1. 흰색 제거, 조건 2. 검은색 제거, 조건 3. 작은수 - 큰수 = 음수 방지
        if int(elec_plate[y,x,2]) - int(elec_plate[y,x,0]) > 50 and np.sum(elec_plate[y,x])>100 and int(elec_plate[y,x,2]) > int(elec_plate[y,x,0]):
            elec_range[y,x] = 255
            isElectronic+=1
        else:
            elec_range[y,x] = 0
            notElectronic+=1

  #cv2.imshow('electronic_license_plate', elec_range)
  #cv2.waitKey()
  #print(isElectronic, notElectronic)


  if 3 * isElectronic >= notElectronic: # 10배(하이퍼 파라미터) 이상 차이가 나면 전기자동차로 인식
      #print("전기 자동차가 검출되었습니다.")
      is_electric_car = 1
  else:
      #print("전기 자동차가 아닙니다.")
      is_electric_car = 0
  
  return is_electric_car
