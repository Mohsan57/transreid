from fastapi import HTTPException, WebSocketDisconnect
from object_detection.detect import ObjectDetection
import cv2
import shutil


class LiveCameraReid():
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.weight = 'object_detection_models/yolov7-tiny.pt'
        self.object_detection = ObjectDetection(self.weight,output_dir=self.base_dir)
        
    def detect_frames(self,frame):
        self.object_detection.detect(source=frame, name="person" )

    def live_reid(self, frame):
        self.detect_frames(frame)
        return



    async def send_camera_frames(self, websocket,ip,username,password):
                # Set up the camera stream
                camera_url = f"http://{username}:{password}@{ip}/video"
                cap = cv2.VideoCapture(camera_url)
                
                # Check if the connection was successful
                if not cap.isOpened():
                    raise HTTPException(status_code=404, detail="Camera not opened")
                

                try:
                    while True:
                        # Read a frame from the camera
                        ret, frame = cap.read()

                        if not ret:
                            # Camera is disconnected
                            raise HTTPException(status_code=404, detail="Camera is stopped!")

                        cv2.imwrite(f"{self.base_dir}/frame.jpg", frame)     # save frame as JPEG file 
                        # Process the frame (if needed)
                        self.live_reid(f"{self.base_dir}/frame.jpg")
                        
                        # Encode the frame as JPEG
                        _, buffer = cv2.imencode(".jpg", frame)

                        
                        # Send the frame as a WebSocket message
                        await websocket.send_bytes(buffer.tobytes())

                except WebSocketDisconnect:
                    # Handle WebSocket disconnection (camera closed by the user)
                    cap.release()
                    # remove Dir
                    try:
                        shutil.rmtree(f"{self.base_dir}/person")
                    except shutil.Error as e:
                        print("Error in Removing files: "+e)
                    await websocket.close()
