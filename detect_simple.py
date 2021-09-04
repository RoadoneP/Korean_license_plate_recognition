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
import pprint
from time import time
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

MODEL_PATH = ['./checkpoints/yolov4-416.tflite','./checkpoints/yolov4-416-disabled.tflite']
# MODEL_PATH = './checkpoints/yolov4-416.tflite'
IOU_THRESHOLD = 0.45
SCORE_THRESHOLD = 0.25
INPUT_SIZE = 416

def Snapshot(loc):
  url = 'rtsp://ID:Password@ip/'
  cap = cv2.VideoCapture(url)

  ret, image = cap.read()

  if not ret:
    print("Snapshot Error!")
    return
  if loc == 1:
    cv2.imwrite('./camera1.jpg', image)
  elif loc == 2:
    cv2.imwrite('./camera2.jpg', image)


def main(img_paths):
  for img_path in img_paths:
    # t = time()
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    img_input = cv2.resize(img, (INPUT_SIZE, INPUT_SIZE))
    img_input = img_input / 255.
    img_input = img_input[np.newaxis, ...].astype(np.float32)
    img_input = tf.constant(img_input)
    for disabled, model_path in enumerate(MODEL_PATH):
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
      
      if disabled == 1:
        if img_path =='camera1.jpg':
          cv2.imwrite('result_disabled1.png', result)
        elif img_path =='camera2.jpg':
          cv2.imwrite('result_disabled2.png', result)
        print("disabled 완료")
      elif disabled == 0:
        if img_path =='camera1.jpg':
          cv2.imwrite('result1.png', result)
        elif img_path =='camera2.jpg':
          cv2.imwrite('result2.png', result)
        image_name = img_path.split('/')[-1]
        image_name = image_name.split('.')[0]

        original_h, original_w, _ = img.shape
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
        #image_path = crop_objects(cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)#, pred_bbox, crop_path, allowed_classes)
        pprint.pprint(jdict, width=20)

if __name__ == '__main__':
    #Snapshot(1)
    #Snapshot(2)
    img_path = ['camera1.jpg','camera2.jpg']
    main(img_path)
