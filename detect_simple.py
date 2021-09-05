import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
import core.utils as utils
from tensorflow.python.saved_model import tag_constants
from core.functions import *
from PIL import Image
from core.yolov4 import filter_boxes
import cv2
import numpy as np
from time import time
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

MODEL_PATH = ['./checkpoints/yolov4-416.tflite','./checkpoints/yolov4-416-disabled.tflite']
# MODEL_PATH = './checkpoints/yolov4-416.tflite'
IOU_THRESHOLD = 0.45
SCORE_THRESHOLD = 0.25
INPUT_SIZE = 416


def detect(img_path, state):
  t = time()
  img = cv2.imread(img_path)
  img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

  img_input = cv2.resize(img, (INPUT_SIZE, INPUT_SIZE))
  img_input = img_input / 255.
  img_input = img_input[np.newaxis, ...].astype(np.float32)
  img_input = tf.constant(img_input)
  # loc 찾기
  print(state)
  if state == "A1" or state == "All":
    selected_model = MODEL_PATH
    print("A1 or All")
  else:
    selected_model = [MODEL_PATH[0]]
    print("A2 or A3")

  for disabled, model_path in enumerate(selected_model):
    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    #print(input_details)
    #print(output_details)
    interpreter.set_tensor(input_details[0]['index'], img_input)
    interpreter.invoke()
    pred = [interpreter.get_tensor(output_details[i]['index']) for i in range(len(output_details))]
    boxes, pred_conf = filter_boxes(pred[0], pred[1], score_threshold=0.25, input_shape=tf.constant([INPUT_SIZE, INPUT_SIZE]))

    boxes, scores, classes, valid_detections = tf.image.combined_non_max_suppression(
        boxes=tf.reshape(boxes, (tf.shape(boxes)[0], -1, 1, 4)),
        scores=tf.reshape(
            pred_conf, (tf.shape(pred_conf)[0], -1, tf.shape(pred_conf)[-1])),
        max_output_size_per_class=50,
        max_total_size=50,
        iou_threshold=IOU_THRESHOLD,
        score_threshold=SCORE_THRESHOLD
    )

    pred_bbox = [boxes.numpy(), scores.numpy(), classes.numpy(), valid_detections.numpy()]
    result = utils.draw_bbox(img, pred_bbox, disabled)
    result = Image.fromarray(result.astype(np.uint8))
    #image.show()
    result = cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)
    original_h, original_w, _ = img.shape
    if disabled == 0:
      if img_path =='./camera/camera1.jpg':
        cv2.imwrite('./result/result1.png', result)
      elif img_path =='./camera/camera2.jpg':
        cv2.imwrite('./result/result2.png', result)
      image_name = img_path.split('/')[-1]
      image_name = image_name.split('.')[0]
      
      bboxes = utils.format_boxes(boxes.numpy()[0], original_h, original_w)

      pred_bbox = [bboxes, scores.numpy()[0], classes.numpy()[0], valid_detections.numpy()[0]]

      allowed_classes = ['license_plate']

      crop_path = './detections/crop/'+image_name
      # print('detect: ',time() - t)
      print("Cropped LP images in '{}' folder location.".format(crop_path))
      try:
          os.mkdir(crop_path)
      except FileExistsError:
          pass
      # ocr
      
      jdict = crop_objects(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), pred_bbox, crop_path, allowed_classes)
    
    elif disabled == 1:
      if img_path =='./camera/camera1.jpg':
        cv2.imwrite('./result/result1.png', result)
      elif img_path =='./camera/camera2.jpg':
        cv2.imwrite('./result/result2.png', result)

      bboxes = utils.format_boxes(boxes.numpy()[0], original_h, original_w)

      # detect "a" disabled Sticker 
      pred_bbox = bboxes[0]

      xmin, _, xmax, _ = pred_bbox

      _, image_w, _ = img.shape
      
      xmin = xmin/image_w
      xmax = xmax/image_w
      center = (xmin + xmax) / 2
      # is disabled Sticker in location "A1"?
      if center > 0 and center < 0.33:
        if(jdict[0]['location'] == 'A1'):
          jdict[0]['disabled_car']=1
      print("disabled 완료")
   
  return jdict


