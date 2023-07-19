from fastapi import WebSocketDisconnect, HTTPException, status
from object_detection.detect import ObjectDetection
from transreid.reid import REID
import os
import cv2
import numpy as np
import shutil
import re
from file_operations import xywh2xyxy

class SyncNetworkController:

    def __init__(self, base_dir, cameras_list, ip_address):
        self.base_dir = base_dir
        self.weight = 'object_detection_models/yolov7-tiny.pt'
        self.is_target_image_set = False
        self.cameras_list = cameras_list
        self.ip_address = ip_address
        
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
        detect_people_with_acc = re.split(r'\s+',str(info_file.read()))
        detect_people_with_acc.pop()
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
        if(len(detect_people_with_acc)>0):
            detect = 0
            detect_people = []
            accuracy = []
            for data in detect_people_with_acc:
                n,a = data.split(",")
                detect_people.append(n)
                accuracy.append(a)
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
                cv2.putText(frame, f'Accuracy: {round(float(accuracy[0])*100,2)}%', (int(box_x1), int(box_y1)-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (36,255,12), 2)
                # if(float(accuracy[0]) >= 0.90):
                #     files = os.listdir(self.base_dir)
                #     for file in files:
                #         if file.startswith("target_image"):
                #             os.remove(f"{self.base_dir}/{file}")
                #     #crop image
                    
                #     cv2.imwrite(f"{self.base_dir}/target_image.jpg", frame)    
                    
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

    async def stream_and_process_frames(self, client, websocket):
        try:
            while(True):
                for camera_id in self.cameras_list:
                    frame = single_camera_stream(client, camera_id)
                    
                    if frame is not None:
                        # Convert frame to JPEG format
                        
                        
                        buffer = self.live_reid(frame=frame,width=720,height=520)
                        
                        jpeg_bytes = buffer.tobytes()
                        # Send the frame and camera ID to all connected WebSocket clients
                        
                        await websocket.send_text(str(camera_id))
                        await websocket.send_bytes(jpeg_bytes)
                    
        except WebSocketDisconnect:       
             await websocket.close()

    



def single_camera_stream(client, camera_id):
        try:
            response = client.Streaming.channels[camera_id].picture(method='get', type='opaque_data')
            
            # Read the image data from the response
            image_data = b""
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    image_data += chunk
                
                # Convert the image data to a numpy array
            image_array = np.frombuffer(image_data, dtype=np.uint8)
            
            
                # Decode the image array using OpenCV
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                
            # Store the frame in the corresponding position in the frames list
            return frame
        except Exception as e:
            print(e)
            return None
