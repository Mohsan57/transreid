from fastapi.security import OAuth2PasswordRequestForm
import OAuth
from fastapi import APIRouter, Depends, status, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from database import get_db
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import cv2
import db_models, schemas
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, NoResultFound
import os
from controller import liveController
import asyncio
router = APIRouter(
    prefix="/live-camera-reid",
    tags=["single-camera-reid"]
)


# Define a route to add a new camera by IP address, username, and password
@router.post("/add_camera",status_code=status.HTTP_200_OK)
async def add_camera(request: schemas.cameras, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):
    try:
        current_user_email = form_data.email
        user = db.query(db_models.User).filter(db_models.User.email == current_user_email).first()
         # Establish a connection to the camera
        camera_url = f"http://{request.username}:{request.password}@{request.ip}/video"
        cap = cv2.VideoCapture(camera_url)

        # Check if the connection was successful
        if not cap.isOpened():
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,  detail="Camera not opened")

        # Read a frame from the video feed
        ret, frame = cap.read()

        # Check if the frame was successfully read
        if not ret:
            cap.release()
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,  detail="Failed to retrieve video feed from the camera.")
        cap.release()
        cv2.destroyAllWindows()
        # store in DB
        try:
            camera = db_models.Camera(user_id = user.id, ip = request.ip, username= request.username, password = request.password)
            db.add(camera)
            db.commit()    
            return  {"Success": [{"Message":"Camera Added Successfuly!"}]}
        except IntegrityError as i:
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,  detail="This IP address already Exist!")
    except Exception:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,  detail="Error During building connection!")
    
# Define a route to remove a camera by IP address
@router.delete("/remove_camera/{ip}", status_code=status.HTTP_200_OK)
async def remove_camera(ip: str, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):
    try:
        current_user_email = form_data.email
        user = db.query(db_models.User).filter(db_models.User.email == current_user_email).first()
        cameras = db.query(db_models.Camera).filter(and_(db_models.Camera.ip.like(ip), db_models.Camera.user_id.like(user.id))).first()
        print(cameras)
        if cameras:
            db.delete(cameras)
            db.commit()
            return  {"Success": [{"Message":"Camera Deleted Successfuly!"}]}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Wrong IP Address")
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Wrong IP Address")


# Define a route to stream a camera's video feed
@router.websocket("/stream_camera/{ip}")
async def stream_camera(websocket: WebSocket, ip: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        # Fetch the camera details from the database
        camera = db.query(db_models.Camera).filter(db_models.Camera.ip.like(ip)).first()
        if camera:
            # Establish a WebSocket connection
            await websocket.accept()
            
            dir = f"live/{camera.user_id}/{camera.id}"
            path = os.path.join("temp/", dir)
            try:
                os.makedirs(path)
            except Exception:
                print("Already exist")
            
            live_camera = liveController.LiveCameraReid(base_dir=path)
            
            await live_camera.send_camera_frames(websocket = websocket ,ip = camera.ip, username = camera.username,password = camera.password)
            # Start the camera frame streaming in the background task
            # background_tasks.add_task(sync_wrapper,websocket,camera.ip, camera.username,camera.password)

        else:
            raise HTTPException(status_code=404, detail="Camera not found!")
    except Exception:
        raise HTTPException(status_code=404, detail="Camera not opened")   
    

def sync_wrapper(websocket,ip, username,password):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(liveController.send_camera_frames(websocket = websocket ,ip = ip, username = username,password = password))
    
    
    
    
# Define a route to list all cameras and their corresponding video stream URLs
@router.get("/list_cameras",status_code=status.HTTP_200_OK)
async def list_cameras(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):
    current_user_email = form_data.email
    user = db.query(db_models.User).filter(db_models.User.email == current_user_email).first()
    cameras = db.query(db_models.Camera).filter(db_models.Camera.user_id == user.id).all()     
    return {"cameras": [{"ip": camera.ip, "username": camera.username} for camera in cameras]}


# cap = None  # Global variable to store the video capture object
# streaming = False  # Global variable to indicate whether the video stream is active
# frame_rate = 7
# prev = 0
# # Route to start the video stream
# @router.get("/start_video_stream")
# async def start_video_stream():
#     global cap, streaming
#     if not streaming:
#         url = f"http://admin:admin@192.168.1.6:8080/video"
#         cap = cv2.VideoCapture(0) # 0 indicates the default camera
#         streaming = True
#         return {"message": "Video stream started."}
#     else:
#         return {"message": "Video stream is already active."}

# # Route to stop the video stream
# @router.get("/stop_video_stream")
# async def stop_video_stream():
#     global cap, streaming
#     if streaming:
#         cap.release()
#         cv2.destroyAllWindows()
#         streaming = False
#         return {"message": "Video stream stopped."}
#     else:
#         return {"message": "Video stream is already stopped."}

# # Route to stream the video
# @router.get("/video_feed")
# async def video_feed():
#     frame_rate = 10
#     prev = 0
    
#     body = cv2.CascadeClassifier('test/haarcascade_frontalface_alt2.xml')

#     global cap, streaming
#     if not streaming:
#         # yield Response("No video stream.", media_type="text/plain")
#         return
#     while streaming:
#         time_elapsed = time.time() - prev
#         res, frame = cap.read()

#         if time_elapsed > 1./frame_rate:
#             prev = time.time()
#             # Convert the frame to grayscale
#             gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

#     # Detect objects in the grayscale frame
#             objects = body.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

#          # Draw bounding boxes around the detected objects
#             for (x, y, w, h) in objects:
#                 cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
#             # Encode the frame as JPEG
#             ret, buffer = cv2.imencode('.jpg', frame)
#             if not ret:
#                 break
#             # Convert the frame to bytes
#             frame_bytes = buffer.tobytes()
#             # Yield the frame as bytes
#             yield (b'--frame\r\n'
#                 b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# # Route to view the stream
# @router.get("/view_video_feed")
# async def view_video_feed():
#     async def content():
#         async for frame in video_feed():
#             yield frame
#     return StreamingResponse(content(), media_type="multipart/x-mixed-replace;boundary=frame")

# # Route to stop the stream
# @router.get("/stop_video_feed")
# async def stop_video_feed():
#     global streaming
#     if streaming:
#         streaming = False
#         return {"message": "Video feed stopped."}
#     else:
#         return {"message": "Video feed is already stopped."}