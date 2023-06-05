from fastapi import APIRouter, File, status, UploadFile, HTTPException
import shutil
from controller.arduinoController import ArduinoController
import os
router = APIRouter(
    prefix="/arduino-test",
    tags = ["Arduino Test"],
    
)

arduino = ArduinoController("users/arduino")

@router.post("/upload-target-image",status_code=status.HTTP_200_OK)
def upload_target_image(target_image: UploadFile = File(title="Target Image",description="Select Target Image")):
    image_extension = target_image.filename.split(".")[-1]
    base_dir = "users/arduino"
    try:
        files = os.listdir(base_dir)
        for file in files:
            if file.startswith("target_image"):
                os.remove(f"{base_dir}/{file}")
    except Exception as e:
        print("Error removing pre target")
    try:
        with open(f"{base_dir}/target_image.{image_extension}", "wb") as buffer:
            shutil.copyfileobj(target_image.file, buffer)
        return {"details":"Successfully upload"}        
    except shutil.ExecError as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File Uploading Error\n{err}")

    
    
@router.get("/arduino-handshake", status_code=status.HTTP_200_OK)
async def handshake():
    return arduino.handshake()

import base64
@router.post("/upload-frame")
async def upload_frame(frame: bytes  = File(...)):
    image_data = base64.b64decode(frame) 
    with open(f'users/arduino/frame.jpg', 'wb+') as f:
            f.write(image_data)
    return arduino.arduino_reid()
