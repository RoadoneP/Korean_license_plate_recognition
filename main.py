import cv2
from detect_simple import detect
import datetime as dt
import pprint

def Snapshot(loc):
  url = 'rtsp://ID:Password@ip/'
  cap = cv2.VideoCapture(url)

  ret, image = cap.read()

  if not ret:
    print("Snapshot Error!")
    return
  # 후에 없앨 것
  if loc == 1:
    cv2.imwrite('./camera/camera1.jpg', image)
  elif loc == 2:
    cv2.imwrite('./camera/camera2.jpg', image)

def mqtt():
  location = "A3"
  In_out = "In"
  return location, In_out

def start():
    loc, In_out = mqtt()
    #Snapshot(1)
    #Snapshot(2)
    img_path = './camera/camera1.jpg'
    jdict = dict()
    # floor if camera1 : B1, camera2 : B2
    # snapshot or In or out
    info = {"parkingLoTIndex" : 1, "floor": "B1", "type" : "snapshot", "createAt": dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    jdict["info"] = info
    data = detect(img_path, loc)
    
    if jdict["info"]["type"] == "snapshot":
      jdict["data"] = data
      pprint.pprint(jdict, width=20)
    elif jdict["info"]["type"] == "In":
      select = int(loc[-1]) - 1
      jdict["data"] = [data[select]]
      pprint.pprint(jdict)
if __name__ == "__main__":
  start()