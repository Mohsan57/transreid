from fastapi.security import OAuth2PasswordRequestForm
import OAuth
from fastapi import APIRouter, Depends, status, Response
from database import get_db
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import cv2
import time


router = APIRouter(
    prefix="/live-camera-reid",
    tags=["single-camera-reid"]
)

# Define dictionaries to store camera IP addresses, video stream objects, and URLs for each camera
cameras = {}
streams = {}

# Define a route to add a new camera by IP address, username, and password
@router.post("/add_camera/{ip}")
async def add_camera(ip: str, username: str = None, password: str = None):
    if ip not in cameras:
        # Create a new video stream object for the camera with the supplied username and password
        cameras[ip] = cv2.VideoCapture(f"http://{username}:{password}@{ip}/video")
        # Add a new URL for the camera's video stream
        streams[ip] = f"/stream_camera/{ip}"
        return {"message": f"Camera {ip} added successfully!"}
    else:
        return {"message": f"Camera {ip} already exists!"}

# Define a route to remove a camera by IP address
@router.delete("/remove_camera/{ip}")
async def remove_camera(ip: str):
    if ip in cameras:
        # Release the video stream object for the camera and remove it from the dictionary
        cv2.destroyAllWindows()
        cameras[ip].release()
        cameras.pop(ip)
        # Remove the URL for the camera's video stream
        print(streams)
        streams.pop(ip)
        return {"message": f"Camera {ip} removed successfully!"}
    else:
        return {"message": f"Camera {ip} does not exist!"}

# Define a route to stream a camera's video feed
@router.get("/stream_camera/{ip}")
async def stream_camera(ip: str):
    if ip in cameras:
        # Define a generator function to read frames from the video stream object and yield them as JPEG images
        def generate_frames():
            while True:
                ret, frame = cameras[ip].read()
                if not ret:
                    break
                _, buffer = cv2.imencode(".jpg", frame)
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        # Return a StreamingResponse object with the generator function as its content
        return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace;boundary=frame")
    else:
        return Response(status_code=404, content="Camera not found!")

# Define a route to list all cameras and their corresponding video stream URLs
@router.get("/list_cameras")
async def list_cameras():
    return {"cameras": [{"ip": ip, "stream_url": streams[ip]} for ip in cameras]}





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