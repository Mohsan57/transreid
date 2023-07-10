from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, WebSocket, WebSocketException
from fastapi.security import OAuth2PasswordRequestForm
import OAuth
from hikvisionapi import Client
from controller.sync_networkController import SyncNetworkController
from database import get_db
from sqlalchemy import and_
import shutil
from sqlalchemy.orm import Session
import db_models, schemas
from sqlalchemy.exc import IntegrityError
import os
import cv2
import numpy as np


router = APIRouter(
    prefix="/sync-camera-network",
    tags=["sync-camera-network"]
)

@router.post("/add-Network", status_code=200)
async def add_Network(network_ip: str, network_username: str, network_password: str,db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):
    try:
        cam = Client(f'http://{network_ip}', network_username, network_password, timeout=10)
            
        # Dict response (default)
        response = cam.System.deviceInfo(method='get')

        response == {
            u'DeviceInfo': {
                u'@version': u'2.0',
                '...':'...'
                }
            }
        current_user_email = form_data.email
        user = db.query(db_models.User).filter(db_models.User.email == current_user_email).first()
        # store in DB
        try:
                network = db_models.Network(user_id = user.id, ip = network_ip, username= network_username, password = network_password)
                db.add(network)
                db.commit()
                db.refresh(network)
                dir = f"network/{user.id}/{network.id}"
                path = os.path.join("users/", dir)
                try:
                    os.makedirs(path)
                except Exception:
                    print("path Already exist")
                return  {"Success": [{"Message":"Network Added Successfuly!"}]}
        except IntegrityError as i:
                raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,  detail="This IP address already Exist!")
        
    except:
        raise HTTPException(status_code=404, detail="DVR Not Found")

@router.delete("/delete-network",status_code=status.HTTP_200_OK)
async def delete_network(network_ip: str,db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):
    try:
        current_user_email = form_data.email
        user = db.query(db_models.User).filter(db_models.User.email == current_user_email).first()
        network = db.query(db_models.Network).filter(and_(db_models.Network.ip.like(network_ip), db_models.Network.user_id.like(user.id))).first()
        print(network)
        if network:
            db.delete(network)
            db.commit()
            return  {"Success": [{"Message":"Camera Deleted Successfuly!"}]}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Wrong IP Address")
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Wrong IP Address")

@router.get("/list-network",status_code=status.HTTP_200_OK)
async def list_network(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):

    try:
        current_user_email = form_data.email
        user = db.query(db_models.User).filter(db_models.User.email == current_user_email).first()
        networks = db.query(db_models.Network).filter(db_models.Network.user_id == user.id).all()
        return {"Networks": [{"ip": network.ip, "username": network.username} for network in networks]}
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Not Found Any Record")

@router.get("/list-camera",status_code=status.HTTP_200_OK)
async def list_camera(network_ip: str,db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):
    
    current_user_email = form_data.email
    user = db.query(db_models.User).filter(db_models.User.email == current_user_email).first()
    network = db.query(db_models.Network).filter(and_(db_models.Network.ip.like(network_ip), db_models.Network.user_id.like(user.id))).first()
    if network:
        try:
            cam = Client(f'http://{network.ip}', network.username, network.password, timeout=10)
            response = cam.Streaming.channels(method='get') 
            channels = response['StreamingChannelList']['StreamingChannel']
            channels_list = []
            for channel in channels:
                i = int(channel['id'])
                if i%100 == 1:
                    channels_list.append(i)
            return {"Cameras": channels_list}
        except:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Could Not Connect To DVR")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Wrong IP Address")

@router.post("/upload-target-image",status_code=status.HTTP_200_OK)
async def upload_target_image(network_ip: str,target_image: UploadFile = File(title="Target Image",description="Select Target Image"),db: Session = Depends(get_db),
                               form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):
    
    image_extension = target_image.filename.split(".")[-1]
    target_image_type = target_image.content_type
    if target_image_type.startswith("image"):
        try:
            current_user_email = form_data.email
            users = db.query(db_models.User).filter(db_models.User.email == current_user_email).first()
            user_id = users.id
            network = db.query(db_models.Network).filter(and_(db_models.Network.ip.like(network_ip), db_models.Camera.user_id.like(user_id))).first()
            if network:
                base_dir = f"users/network/{user_id}/{network.id}"
                files = os.listdir(base_dir)
                for file in files:
                    if file.startswith("target_image"):
                        os.remove(f"{base_dir}/{file}")
                try:
                    base_dir = f"users/network/{user_id}/{network.id}"
                    with open(f"{base_dir}/target_image.{image_extension}", "wb") as buffer:
                        shutil.copyfileobj(target_image.file, buffer)
                    return {"details":"Successfully upload"}        
                except shutil.ExecError as err:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File Uploading Error\n{err}")
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network IP is Invalid")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network IP is Invalid")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type is not supported")


# Define a route to stream a camera's video feed
@router.websocket("/stream_network/{ip}/camera/{camera_ids}")
async def stream_camera(websocket: WebSocket ,ip: str, camera_ids: str, db: Session = Depends(get_db)):
    try:
        camera_id_list = [int(cid) for cid in camera_ids.split(",")]
        print(camera_id_list)
        # Fetch the camera details from the database
        network = db.query(db_models.Network).filter(db_models.Network.ip.like(ip)).first()
        
        if network:
            print("network")
            cam = Client(f'http://{network.ip}', network.username, network.password, timeout=10)
            
            # Dict response (default)
            response = cam.System.deviceInfo(method='get')
            response == {
                u'DeviceInfo': {
                    u'@version': u'2.0',
                    '...':'...'
                    }
                }
            
            # Establish a WebSocket connection
            await websocket.accept()
            
            dir = f"network/{network.user_id}/{network.id}"
            path = os.path.join("users/", dir)
            try:
                os.makedirs(path)
            except Exception:
                print("path Already exist")
            
            #stream_all_cameras(cam, camera_ids)
            base_dir = f"users/network/{network.user_id}/{network.id}"
            live_network = SyncNetworkController(base_dir=base_dir, cameras_list=camera_id_list ,ip_address = network.ip)
            await live_network.stream_and_process_frames(cam,websocket)
            
            

        else:
            print(
                f"Network IP address {ip} not found in the database!"
            )
            raise HTTPException(status_code=404, detail=f"Network IP address {ip} not found")
        
    except Exception:
        raise HTTPException(status_code=404, detail="Could Not Connect To DVR") 



def stream_all_cameras(client, camera_ids):
    
    response = client.Streaming.channels(method='get')
    channels = []
    for channel in response['StreamingChannelList']['StreamingChannel']:
        if int(channel['id']) in camera_ids:
            channels.append(channel)
    
    # Get the total number of channels
    num_channels = len(channels)
    
    # Calculate the number of rows and columns to divide the window
    rows = int(np.sqrt(num_channels))
    cols = int(np.ceil(num_channels / rows))
    
    # Create the window to display the streams from all channels
    cv2.namedWindow('Camera Streams', cv2.WINDOW_NORMAL)
    
    # Initialize an empty frame for each channel
    frames = [None] * num_channels
    
    while True:
        # Retrieve the frames from each camera channel
        for i, channel in enumerate(channels):
            channel_number = channel['id']
            response = client.Streaming.channels[channel_number].picture(method='get', type='opaque_data')
            
            # Read the image data from the response
            image_data = b""
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    image_data += chunk
            
            # Convert the image data to a numpy array
            image_array = np.frombuffer(image_data, dtype=np.uint8)
            
            # Decode the image array using OpenCV
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            # Resize the frame to fit the window section
            frame = cv2.resize(frame, (int(1280/cols), int(720/rows)))
            
            # Store the frame in the corresponding position in the frames list
            frames[i] = frame
        
        # Create an empty canvas to display the frames
        canvas = np.zeros((720, 1280, 3), dtype=np.uint8)
        
        # Divide the canvas into sections and display the frames
        for i, frame in enumerate(frames):
            row = i // cols
            col = i % cols
            
            x = int(col * (1280/cols))
            y = int(row * (720/rows))
            
            canvas[y:y+int(720/rows), x:x+int(1280/cols)] = frame
        
        # Display the canvas in the window
        cv2.imshow('Camera Streams', canvas)
        
        if cv2.waitKey(1) == ord('q'):
            break
    
    cv2.destroyAllWindows()