from fastapi import APIRouter, File, status
from controller.arduinoController import ArduinoController
router = APIRouter(
    prefix="/arduino-test",
    tags = ["Arduino Test"],
    
)

arduino = ArduinoController("users/arduino")

@router.get("/arduino-handshake", status_code=status.HTTP_200_OK)
async def handshake():
    return arduino.handshake()

@router.post("/upload-frame")
async def upload_frame(frame: bytes = File(...)):
   return arduino.arduino_reid(frame=frame)
