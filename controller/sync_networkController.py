from fastapi import WebSocketDisconnect
from object_detection.detect import ObjectDetection
from transreid.reid import REID
import os
import cv2
import numpy as np
import json

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

    async def stream_and_process_frames(self, client, websocket):
        try:
            
            while(True):
                for camera_id in self.cameras_list:
                    frame = single_camera_stream(client, camera_id)
                    
                    if frame is not None:
                        # Convert frame to JPEG format
                        _, buffer = cv2.imencode('.jpg', frame)
                        
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
