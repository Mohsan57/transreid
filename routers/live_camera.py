import asyncio
from fastapi.security import OAuth2PasswordRequestForm
import OAuth
from fastapi import APIRouter, Depends, Query, status, BackgroundTasks, HTTPException, WebSocket, UploadFile, File
from database import get_db
from sqlalchemy.orm import Session
import cv2
import db_models, schemas
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
import os
from controller.liveController import LiveCameraReid
import shutil
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

        # Check if the connection was not successful
        if not cap.isOpened():
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,  detail="Camera not opened")

        # Read a frame from the video feed
        ret, frame = cap.read()

        # Check if the frame was successfully read
        if not ret:
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,  detail="Failed to retrieve video feed from the camera.")
        cap.release()
        cv2.destroyAllWindows()
        # store in DB
        try:
            camera = db_models.Camera(user_id = user.id, ip = request.ip, username= request.username, password = request.password)
            db.add(camera)
            db.commit()
            db.refresh(camera)
            dir = f"live/{user.id}/{camera.id}"
            path = os.path.join("users/", dir)
            try:
                os.makedirs(path)
            except Exception:
                print("path Already exist")
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

@router.get("/get-total-cameras", status_code=status.HTTP_200_OK)
async def get_total_cameras(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):
    try:
        current_user_email = form_data.email
        user = db.query(db_models.User).filter(db_models.User.email == current_user_email).first()
        cameras = db.query(db_models.Camera).filter(db_models.Camera.user_id == user.id).all()
        return {"total_cameras": len(cameras)}
    except Exception:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail="Something went wrong")


# upload target image for REID
@router.post("/upload-target-image",status_code=status.HTTP_200_OK)
async def upload_target_image(camera_ip: str,target_image: UploadFile = File(title="Target Image",description="Select Target Image"),db: Session = Depends(get_db),
                               form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):
    
    image_extension = target_image.filename.split(".")[-1]
    target_image_type = target_image.content_type
    if target_image_type.startswith("image"):
        base_dir = ""
        try:
            current_user_email = form_data.email
            users = db.query(db_models.User).filter(db_models.User.email == current_user_email).first()
            user_id = users.id
            camera = db.query(db_models.Camera).filter(and_(db_models.Camera.ip.like(camera_ip), db_models.Camera.user_id.like(user_id))).first()
            if camera:
                camera_id = camera.id
                base_dir = f"users/live/{user_id}/{camera_id}"
                files = os.listdir(base_dir)
                for file in files:
                    if file.startswith("target_image"):
                        os.remove(f"{base_dir}/{file}")
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera IP is Invalid")
        except Exception as e:
            print("Error removing already target image")
        try:
            with open(f"{base_dir}/target_image.{image_extension}", "wb") as buffer:
                shutil.copyfileobj(target_image.file, buffer)
            return {"details":"Successfully upload"}        
        except shutil.ExecError as err:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File Uploading Error\n{err}")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type is not supported")

    
# Define a route to stream a camera's video feed
@router.websocket("/stream_camera/{ip}")
async def stream_camera(websocket: WebSocket, ip: str, db: Session = Depends(get_db)):
    try:
        # Fetch the camera details from the database
        camera = db.query(db_models.Camera).filter(db_models.Camera.ip.like(ip)).first()
        
        if camera:
            # Establish a WebSocket connection
            await websocket.accept()
            
            dir = f"live/{camera.user_id}/{camera.id}"
            path = os.path.join("users/", dir)
            try:
                os.makedirs(path)
            except Exception:
                print("path Already exist")
            camera_url = f"http://{camera.username}:{camera.password}@{camera.ip}/video"
            cap = cv2.VideoCapture(camera_url)

            # Check if the connection was successful
            if not cap.isOpened():
                raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,  detail="Camera not opened")
            
            cap.release()
            
            live_camera = LiveCameraReid(base_dir=path)
            
            await live_camera.stream_and_process_frames(websocket = websocket ,ip = camera.ip, username = camera.username,password = camera.password)
            

        else:
            print(
                f"Camera with IP address {ip} not found in the database!"
            )
            raise HTTPException(status_code=404, detail="Camera not found!")
        
    except Exception:
        raise HTTPException(status_code=404, detail="Camera not opened") 

# Define a route to list all cameras and their corresponding video stream URLs
@router.get("/list_cameras",status_code=status.HTTP_200_OK)
async def list_cameras(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):
    current_user_email = form_data.email
    user = db.query(db_models.User).filter(db_models.User.email == current_user_email).first()
    cameras = db.query(db_models.Camera).filter(db_models.Camera.user_id == user.id).all()     
    return {"cameras": [{"ip": camera.ip, "username": camera.username} for camera in cameras]}

