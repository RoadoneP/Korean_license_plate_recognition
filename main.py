import cv2
from detect_simple import detect
import datetime as dt
import pprint

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

def mqtt():
  location = "A1"
  In_out = "In"
  floor = "B1"
  return location, In_out, floor

def start():
    loc, In_out, floor = mqtt()
    #img_path = detect_Snapshot(floor)
    img_path = './camera/camera1.jpg'
    jdict = dict()
    # floor if camera1 : B1, camera2 : B2
    # snapshot or In or out
    info = {"parkingLoTIndex" : 1, "floor": floor, "type" : In_out, "createAt": dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    jdict["info"] = info


    data = detect(img_path, loc)
    
    # 로직은 우선 다찍고, snapshot의 경우 data전부를 보내주고
    # 정기적으로 찍는 snapshot
    if jdict["info"]["type"] == "snapshot":
      jdict["data"] = data
      pprint.pprint(jdict, width=20)

    # In인 경우, data[select = 특정 구역]
    elif jdict["info"]["type"] == "In":
      select = int(loc[-1]) - 1 # A1 = 0, A2 = 1, A3 = 2
      jdict["data"] = [data[select]]
      pprint.pprint(jdict)

    # Out인 경우, loaction만 보내준다.
    elif jdict["info"]["type"] == "Out":
      select = int(loc[-1]) - 1 # A1 = 0, A2 = 1, A3 = 2
      if "carNum" in data[select]:
         print("OutError")
      else:
        data = {'loaction' : loc}
        jdict["data"] = [data]
      pprint.pprint(jdict)  
if __name__ == "__main__":
  start()
