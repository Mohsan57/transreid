from object_detection.detect import ObjectDetection
from transreid.reid import REID
import os
import cv2
from file_operations import xywh2xyxy
import shutil
import numpy as np
import re
class ArduinoController():
    def __init__(self, base_dir):
        self.object_detection = None
        self.reid = None
        self.base_dir = base_dir
        self.is_target_image_set = False
        self.is_handshake = False
    
    def handshake(self):
        weight = 'object_detection_models/yolov7-tiny.pt'
        filename = 'target_image'

        # get list of all files in the specified directory
        files = os.listdir(self.base_dir)

        # loop through each file and check for 'target_image' with an image extension
        image_extensions = ['.jpg', '.png', '.jpeg']
        for file in files:
            if file.startswith(filename) and os.path.splitext(file)[1] in image_extensions:
                extension = file.split('.')[1]
                self.object_detection = ObjectDetection(weights=weight,output_dir=self.base_dir)
                self.reid = REID(base_dir=self.base_dir,image_extension=extension)
                self.is_target_image_set = True
                self.is_handshake = True
                return {"handShake":"Accepted"}
        
        return {"HandShake":"Rejected", "details":"First upload target Image"}
    
    def arduino_reid(self, frame):
        if(self.is_handshake == False):
            return {"details":"First call handshake"}
        if(self.is_target_image_set == False):
            return {"details":"First upload target Image"}
        with open(f'{self.base_dir}/frame.jpg', 'wb+') as f:
            f.write(frame)
        frame  = cv2.imread(f"{self.base_dir}/frame.jpg")
        height, width, _ = frame.shape
        
        frame_center_y = int(height)/2
        frame_center_x = int(width)/2
        
        self.object_detection.detect(source=f"{self.base_dir}/frame.jpg")
        self.reid.idetification()
        labels_path = f'{self.base_dir}/person/labels'
        label = f"{labels_path}/frame.txt"
        info_file = open(f"{self.base_dir}/identified_people/information.txt",'r')
        detect_people = re.split(r'\s+',str(info_file.read()))
        detect_people.pop()
        label_file = open(label)
        Lines_in_one_label = str(label_file.read()).split("\n")
        Lines_in_one_label.pop()
        rec_x = ""
        rec_y = ""
        rec_w = ""
        rec_h = ""
        box_x1,box_x2,box_y1, box_y2 = 0,0,0,0
        
        if(len(detect_people)>0):
            detect = 0
            for people in detect_people:
                for line in Lines_in_one_label:
                    file_name, zero, x, y, w, h = re.split(r"\s+",line)
                    str1 = file_name.split("/")
                            
                    if people == str1[-1]:
                        rec_x = x
                        rec_y = y
                        rec_w = w
                        rec_h = h
                        detect = 1
                        
            if(detect == 1):
                xywh = [float(rec_x),float(rec_y), float(rec_w), float(rec_h)]
                
                xywh = np.array(xywh)
                xyxy = xywh2xyxy(xywh)
                
                box_x1 = (xyxy[0]*width )
                box_y1 = (xyxy[1]*height)
                box_x2 = (xyxy[2]*width)
                box_y2 = (xyxy[3]*height)
                print(f"{box_x1}, {box_y1},      \n{box_x2},{box_y2}")
                
                
                
        label_file.close()
        info_file.close()
        try:
            shutil.rmtree(f"{self.base_dir}/person")
            os.remove(f"{self.base_dir}/frame.jpg")
        except shutil.Error as e:
            print("Error in Removing files: "+e)  
         # Encode the frame as JPEG
        cv2.destroyAllWindows()
        
        object_center_x = (box_x1 + box_x2) / 2
        object_center_y = (box_y1 + box_y2) / 2
        deviation_x = object_center_x - frame_center_x
        deviation_y = object_center_y - frame_center_y

        mapped_x = map_value(deviation_x, -frame_center_x, frame_center_x, 0, 180)
        mapped_y = map_value(deviation_y, -frame_center_y, frame_center_y, 0, 180)

        return {"Details":[{
            "mapped_x":mapped_x,
            "mapped_y":mapped_y
        }]}
    
def map_value(value, in_min, in_max, out_min, out_max):
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
