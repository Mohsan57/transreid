import base64
import os

from fastapi import APIRouter, Depends, status, Response, HTTPException, Header,BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
import OAuth
from database import get_db
from sqlalchemy.orm import Session
from fastapi import File, UploadFile, Query
from controller import videoController
from fastapi.responses import FileResponse, StreamingResponse
import db_models
import smtplib
from database import engine
from email_sender import send_email
router = APIRouter(
    prefix="/video-reid",
    tags=["video-reid"]
)

from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="templates")


queue = []  # initialize empty task queue

current_task = {"id": None, "queue": []}  # initialize current task to None

import setting

@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_video_and_target( background_tasks: BackgroundTasks,
    video: UploadFile = File(title="Upload Video",description="Select Video File"),
    target_image: UploadFile = File(title="Target Image",description="Select Target Image") ,
    accuracy : str= Query("low", enum = ["low", "medium","high"],description="Select Accuracy"),
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):

    target_image_type = target_image.content_type
    video_type = video.content_type
    
    if target_image_type.startswith("image") and video_type.startswith("video"):
        if video.size <= setting.INPUT_VIDEO_SIZE_IN_BYTES:
            global current_task
            global queue
            if len(queue) >= setting.QUEUE_LENGTH:
                return {"message": "Task queue is full. Please try again later."}
            
            current_user_email = form_data.email
            device = "cpu"
            users = db.query(db_models.User).filter(db_models.User.email == current_user_email).first()
            user_id = users.id
            dir_name = videoController.make_dir(user_id=user_id)

            base_dir = f'users/{user_id}/{dir_name}'
            videoController.dir_info_file(base_dir = base_dir,accuracy=accuracy)
            
            videoController.upload_video(base_dir=base_dir, video= video, target_image=target_image)
            video_extension = video.filename.split(".")[-1]
            image_extension = target_image.filename.split(".")[-1]
            video_url = f"{base_dir}/org_video.{video_extension}"
            task_id = len(queue) + 1  # assign unique ID to task
            # async with asyncio.wait():  # use lock to modify shared variables safely
            queue.append(task_id)  # add task to queue
                        
            objects = {"device":device,"base_dir": base_dir,
                    "video_url":video_url,"accuracy":accuracy,
                    "task_id":task_id,"user_email":current_user_email,"username":users.name, 
                    "user_id":user_id,"image_extension":image_extension}
                
            if current_task["id"] is None:  # start the task immediately if there is no current task
                    current_task["id"] = task_id
                    current_task["task"] =  background_tasks.add_task(backgroud_process,objects["device"],objects["base_dir"],objects["video_url"],objects["accuracy"],objects["user_email"],
                                                                      objects["username"],objects["user_id"],objects["task_id"],objects["image_extension"])
                            
            else:
                    # add the task ID to the current task's queue
                    current_task["queue"].append(objects)
            video.close()
            return {"Message":f"Your task is being processed. Your task is in queue number {task_id}. After completion, the video will be sent to your Email address",
                            "email": f"{current_user_email}"}
        else:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Video size will not exceed {setting.INPUT_VIDEO_SIZE_IN_BYTES/1000000}MB")
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Please Upload Only Video and Image")
    

def backgroud_process(device,base_dir,video_url,accuracy,user_email,username,user_id,task_id,image_extension):
    
    
    video_url = videoController.reid(device=device, base_dir=base_dir, video_url=video_url, accuracy=accuracy,image_extension=image_extension)
    task_completed_send_mail(result=video_url,base_dir=base_dir,image_extension= image_extension,receiver_email=user_email,username=username,user_id=user_id)
    global current_task
    if current_task["id"] == task_id:
            current_task["id"] = None  # mark the current task as completed
            queue.remove(task_id)
            
            # start the next task if there is one in the queue
            if len(current_task["queue"]) > 0:
                next_task_objects = current_task["queue"].pop(0)
                        
                current_task["id"] = next_task_objects["task_id"]
                current_task["task"] = backgroud_process(device= next_task_objects["device"],base_dir= next_task_objects["base_dir"],
                                                                            video_url= next_task_objects["video_url"],accuracy= next_task_objects["accuracy"],
                                                                            user_email=next_task_objects["user_email"],username=next_task_objects["username"],user_id=next_task_objects["user_id"]
                                                                            ,task_id=next_task_objects["task_id"], image_extension=next_task_objects["image_extension"])
            
def task_completed_send_mail(result,base_dir,image_extension,receiver_email,username,user_id):
    image_name = videoController.get_random_str()
    new_video = db_models.Reid_Video(user_id = user_id,video_name = result ,video_path = f"{base_dir}/output_video.mp4",img_name = image_name,img_path = f"{base_dir}/target_image.{image_extension}")
    session = Session(bind=engine)
    session.add(new_video)
    session.commit()
    session.refresh(new_video)
    try:
        respose = send_email(receiver_email=receiver_email,user_name=username,video_link=result)
        success = db_models.Error(error_code = '200', error_message =f"Successfuly send video link: {result}",receiver_email = receiver_email)
        session.add(success)
        session.commit()
        session.refresh(success)
    except smtplib.SMTPServerDisconnected as er:
        error = db_models.Error(error_code = er.errno , error_message = f" 'SMTPServerDisconnected' {er}",receiver_email = receiver_email)
        session.add(error)
        session.commit()
        session.refresh(error)
    except smtplib.SMTPAuthenticationError as er:
        error = db_models.Error(error_code = er.smtp_code , error_message =f" 'SMTPAuthenticationError' {er}",receiver_email = receiver_email)
        session.add(error)
        session.commit()
        session.refresh(error)
    except smtplib.SMTPSenderRefused as er:
        error = db_models.Error(error_code = er.smtp_code , error_message = f"'SMTPSenderRefused' {er}",receiver_email = receiver_email)
        session.add(error)
        session.commit()
        session.refresh(error)
    except smtplib.SMTPResponseException as er:
        error = db_models.Error(error_code = er.smtp_code , error_message = f"'SMTPResponseException' {er}",receiver_email = receiver_email)
        
        session.add(error)
        session.commit()
        session.refresh(error)

    session.close()
    print(f"Task completed and email sent to {receiver_email}")


@router.get("/download_video/{file_id}",status_code=status.HTTP_200_OK)
async def download_video(file_id: str, db: Session = Depends(get_db)):
    
    video = db.query(db_models.Reid_Video).filter(db_models.Reid_Video.video_name == file_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid Video ID")
    video_path = video.video_path
    return FileResponse(path=video_path, media_type='application/octet-stream', filename='video.mp4')


@router.get('/target-image/{link}')
async def get_target_image (request: Request,link: str, db:Session = Depends(get_db)):
    image = db.query(db_models.Reid_Video).filter(db_models.Reid_Video.img_name == link).first()
    if image:
        file_path = image.img_path
        with open(file_path, "rb") as imageFile:
            str = base64.b64encode(imageFile.read()).decode("utf-8")
            
        return templates.TemplateResponse("image_view.html", {"request": request,"img": str})
       
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=("Invalid link"))


@router.get("/history",status_code=status.HTTP_200_OK)
async def video_history( db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):
    current_user_email = form_data.email
    info = db.query(db_models.Reid_Video).join(db_models.User, db_models.User.id == db_models.Reid_Video.user_id).filter(db_models.User.email == current_user_email).all()
    history = []
    if info:
        for row in info:
            img_path = row.img_path
            str = img_path.split("/")
            
            with open(f"{str[0]}/{str[1]}/{str[2]}/info.txt") as file:
                line = file.readlines()
            created_at = line[0]
            print(created_at)
            created_date = created_at.split(" ")[2]
            created_time =  created_at.split(" ")[3]
            created_time = created_time.replace("\n","")
            accuracy = (line[1].split(": ")[-1])
            accuracy =  accuracy.replace("\n","")
            temp_dict = {"accuracy":accuracy,"created date": created_date, "created time":created_time,"video":row.video_name,"image":row.img_name}
            history.append({str[2]:temp_dict})
    
            
        
    return {"History":history}
        
