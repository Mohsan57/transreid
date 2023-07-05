from fastapi import HTTPException, WebSocketDisconnect
from object_detection.detect import ObjectDetection
from transreid.reid import REID
import cv2
import shutil
import os
import re
import numpy as np 
from file_operations import xywh2xyxy
class LiveCameraReid():
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.weight = 'object_detection_models/yolov7-tiny.pt'
        self.is_target_image_set = False
        
        filename = 'target_image'

        # get list of all files in the specified directory
        files = os.listdir(base_dir)

        # loop through each file and check for 'target_image' with an image extension
        image_extensions = ['.jpg', '.png', '.jpeg']
        for file in files:
            if file.startswith(filename) and os.path.splitext(file)[1] in image_extensions:
                extension = file.split('.')[1]
                
                self.object_detection = ObjectDetection(self.weight,output_dir=self.base_dir)
                
                self.reid = REID(self.base_dir,extension)
                self.is_target_image_set = True
                
            
        if self.is_target_image_set == False:
            print('Target image does not exist')
        
        
        
        
    def live_reid(self, frame, width, height):
        if(self.is_target_image_set == False):
            _, buffer = cv2.imencode(".jpg", frame)
            return buffer
        cv2.imwrite(f"{self.base_dir}/frame.jpg", frame)     # save frame as JPEG file 
        self.object_detection.detect(source=f"{self.base_dir}/frame.jpg")
        
        self.reid.idetification()
        labels_path = f'{self.base_dir}/person/labels'
        label = f"{labels_path}/frame.txt"
        info_file = open(f"{self.base_dir}/identified_people/information.txt",'r')
        detect_people = re.split(r'\s+',str(info_file.read()))
        detect_people.pop()
        is_label_exist = False
        try:
            label_file = open(label)
            is_label_exist = True
        except:
            is_label_exist = False
        
        if(is_label_exist == False):
            info_file.close()
            try:
                shutil.rmtree(f"{self.base_dir}/person")
            except shutil.Error as e:
                print("Error in Removing files: "+e)
             # Encode the frame as JPEG
            _, buffer = cv2.imencode(".jpg", frame)
            cv2.destroyAllWindows()
            return buffer
        Lines_in_one_label = str(label_file.read()).split("\n")
        Lines_in_one_label.pop()
        rec_x = ""
        rec_y = ""
        rec_w = ""
        rec_h = ""
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
                cv2.rectangle(frame, (int(box_x1), int(box_y1)), (int(box_x2), int(box_y2)), (0, 0, 255), 2)
                
                
        label_file.close()
        info_file.close()
        try:
            shutil.rmtree(f"{self.base_dir}/person")
        except shutil.Error as e:
            print("Error in Removing files: "+e)  
         # Encode the frame as JPEG
        _, buffer = cv2.imencode(".jpg", frame)
        cv2.destroyAllWindows()
        return buffer



    async def send_camera_frames(self, websocket,ip,username,password):
                # Set up the camera stream
                camera_url = f"http://{username}:{password}@{ip}/video"
                cap = cv2.VideoCapture(camera_url)
                
                # Check if the connection was successful
                if not cap.isOpened():
                    raise HTTPException(status_code=404, detail="Camera not opened")
                try:
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    while True:
                        # Read a frame from the camera
                        ret, frame = cap.read()

                        if not ret:
                            # Camera is disconnected
                            try:
                                shutil.rmtree(f"{self.base_dir}/person")
                                shutil.rmtree(f"{self.base_dir}/identified_people")
                                print("Camera is disconnected...")
                            except shutil.Error as e:
                                print("Error in Removing files: "+e)
                            await websocket.close()

                            raise HTTPException(status_code=404, detail="Camera is stopped!")
                        
                        
                            # Process the frame (if needed)
                        buffer = self.live_reid(frame=frame,width=width,height=height)
                        
                        await websocket.send_bytes(buffer.tobytes())
                       
                      
                except WebSocketDisconnect:
                    # Handle WebSocket disconnection (camera closed by the user)
                    cap.release()
                    # remove Dir
                    try:
                        shutil.rmtree(f"{self.base_dir}/person")
                        shutil.rmtree(f"{self.base_dir}/identified_people")
                    except shutil.Error as e:
                        print("Error in Removing files: "+e)
                    await websocket.close()
