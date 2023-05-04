from fastapi import APIRouter, Depends, status, Response, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
import OAuth
from database import get_db
from sqlalchemy.orm import Session
from fastapi import File, UploadFile, Query
from controller import videoController
from fastapi.responses import FileResponse

router = APIRouter(
    prefix="/video-reid",
    tags=["video-reid"]
)




@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_video_and_target(
    video: UploadFile = File(title="Upload Video",description="Select Video File"),
    target_image: UploadFile = File(title="Target Image",description="Select Target Image") ,
    accuracy : str= Query("low", enum = ["low", "medium","heigh"],description="Select Accuracy"),
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):
    current_user_email = form_data.email
    device = "cpu"
    output_video = videoController.detect_using_video(db=db,device=device,current_user_email=current_user_email,video=video,target_image=target_image,accuracy=accuracy)
    return FileResponse(path=output_video, media_type='application/octet-stream', filename='video.mp4')

@router.get("/history",status_code=status.HTTP_200_OK)
async def video_history( db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):
    current_user_email = form_data.email
    return videoController.history(db=db, current_user_email=current_user_email)