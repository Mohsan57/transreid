import cv2
import glob
import torch
import numpy as np
import re
from file_operations import xywh2xyxy

            
 
# create VideoCapture object

class Make_ReID_Video:
    def __init__(self,base_dir, video_extention):
        self.base_dir = base_dir
        self.Detect_people_file_names = f'{base_dir}/identified_people/information.txt'
        self.labels_path = f'{base_dir}/person/labels'
        self.store_frame_info_name = f'{base_dir}/detect_person_frames.txt'
        self.cap = cv2.VideoCapture(f'{base_dir}/video.{video_extention}')
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        # create VideoWriter object
        self.out = cv2.VideoWriter(f'{base_dir}/output_video.mp4', cv2.VideoWriter_fourcc(*'mp4v'), self.fps, (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    
            
    def detect_people(self):
        file = open(self.store_frame_info_name, 'r')
        content = (file.read()).split("\n")
        content.pop()
        content_len = len(content)

        # Extract all the numbers from the content
        i = 0
        # loop through each frame of the video
        while self.cap.isOpened():
            # read frame
            ret, frame = self.cap.read()
            
            # check if frame was successfully read
            if ret:
                if( i < content_len):
                    line = content[i]
                    if(line != "break"):
                        x,y,w,h = re.findall(r'\d\.\d+', line)
                        xywh = [float(x),float(y), float(w), float(h)]
                        xywh = np.array(xywh)
                        xyxy = xywh2xyxy(xywh)
                        box_x1 = (xyxy[0]*self.width )
                        box_y1 = (xyxy[1]*self.height)
                        box_x2 = (xyxy[2]*self.width)
                        box_y2 = (xyxy[3]*self.height)
                    
                        cv2.rectangle(frame, (int(box_x1), int(box_y1)), (int(box_x2), int(box_y2)), (0, 0, 255), 2)
                self.out.write(frame)
                i+=1
                # pause between frames
                if cv2.waitKey() & 0xFF == ord('q'):
                    break
            else:
                break

        # release VideoCapture and VideoWriter objects

        self.cap.release()
        self.out.release()

        cv2.destroyAllWindows()

    def make_video(self):
        try:
            labels = []
            
            labels = glob.glob(f"{self.labels_path}/*.txt")
            # print(labels)
           #error
           # Regular expression to extract number
            pattern = r'video_(\d+)\.txt'

            # Loop through the list and extract number from each string
            label_files_number = []
            for s in labels:
                match = re.search(pattern, s)
                
                if match:
                    number = match.group(1)
                    label_files_number.append(int(number))
            label_files_number_sort = sorted(label_files_number)
            
            #labels = sorted(labels, key=lambda x: int(x[36:-4]))
            labels = []
            for n in label_files_number_sort:
                labels.append(f"{self.base_dir}/person/labels/video_{n}.txt")
            
            info_file = open(self.Detect_people_file_names,'r')

            detect_people = re.split(r'\s+',str(info_file.read()))
            detect_people.pop()
            
            detect_people = sorted(detect_people, key=lambda x: int(x[5:-4]))
            file = open(self.store_frame_info_name,"w")
            
            for label in labels:
                detect = 0
                label_file = open(label)
                Lines_in_one_label = str(label_file.read()).split("\n") 
                Lines_in_one_label.pop()
                detect_people = sorted(detect_people, key=lambda x: int(x[5:-4]))
                
                for people in detect_people:
                    for line in Lines_in_one_label:
                        file_name, zero, x, y, w, h = re.split(r"\s+",line)
                        str1 = file_name.split("/")
                        
                        if people == str1[-1]:
                            file.write(f"{x},{y},{w},{h}\n")
                            detect = 1
                    if detect == 1:
                        break
                if(detect == 0):
                    file.write("break\n")
            file.close()
            self.detect_people()
            return True
        except:
            return False
