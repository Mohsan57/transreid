from fastapi import APIRouter, Depends, status, Response, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
import OAuth
from database import get_db
from sqlalchemy.orm import Session
from fastapi import File, UploadFile, Query
from controller import videoController
from fastapi.responses import FileResponse
import db_models
import asyncio
import smtplib
from database import engine, Base
from email_sender import send_email
from controller.queue import queue, current_task, task_completed_event
router = APIRouter(
    prefix="/video-reid",
    tags=["video-reid"]
)



@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_video_and_target(
    video: UploadFile = File(title="Upload Video",description="Select Video File"),
    target_image: UploadFile = File(title="Target Image",description="Select Target Image") ,
    accuracy : str= Query("low", enum = ["low", "medium","high"],description="Select Accuracy"),
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):

    target_image_type = target_image.content_type
    video_type = video.content_type
    
    if target_image_type.startswith("image") and video_type.startswith("video"):
        if video.size <= 15000000:
            global current_task
            global queue
            if len(queue) >= 3:
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
            video_url = f"{base_dir}/org_video.{video_extension}"
            task_id = len(queue) + 1  # assign unique ID to task
            queue.append(task_id)  # add task to queue
                    
            objects = {"device":device,"base_dir": base_dir,
                "video_url":video_url,"accuracy":accuracy,
                "task_id":task_id,"user_email":current_user_email,"username":users.name}
            
            if current_task["id"] is None:  # start the task immediately if there is no current task
                current_task["id"] = task_id
                current_task["task"] = asyncio.create_task(backgroud_process(device,base_dir,video_url,accuracy,current_user_email,users.name,task_id))
                        
            else:
                print("RUN")
                # add the task ID to the current task's queue
                current_task["queue"].append(objects)
            video.close()
            print(queue)
            print(current_task)
            return {"Message":f"Your task is being processed. Your task is in queue number {task_id}. After completion, the video will be sent to your Email address",
                            "email": f"{current_user_email}"}
        else:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Video size will not exceed 15MB")
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Please Upload Only Video and Image")
    
    
    # try:
        # output = videoController.detect_using_video(db=db,device=device,current_user_email=current_user_email,video=video,target_image=target_image,accuracy=accuracy)
        # return output
    # except Exception:
        # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Error in videoController.detect_using_video")


async def backgroud_process(device,base_dir,video_url,accuracy,user_email,username,task_id):
    await asyncio.sleep(5)
    global_video_url = await videoController.reid(device=device,base_dir=base_dir,video_url=video_url,accuracy=accuracy)
    global current_task
    if current_task["id"] == task_id:
        current_task["id"] = None  # mark the current task as completed
        queue.remove(task_id)
            
        # start the next task if there is one in the queue
        if len(current_task["queue"]) > 0:
            next_task_objects = current_task["queue"].pop(0)
                    
            current_task["id"] = next_task_objects["task_id"]
            current_task["task"] = asyncio.create_task(backgroud_process(device= next_task_objects["device"],base_dir= next_task_objects["base_dir"],
                                                                         video_url= next_task_objects["video_url"],accuracy= next_task_objects["accuracy"],
                                                                          user_email=next_task_objects["user_email"],username=next_task_objects["username"]
                                                                          ,task_id=next_task_objects["task_id"]))
        
        task_completed_callback(result= global_video_url,base_dir= base_dir,receiver_email=user_email,username= username)
        task_completed_event.set()  # set the event to signal task completion


def task_completed_callback(result,base_dir,receiver_email,username):
    # await task_completed_event.wait()
    new_video = db_models.reid_video(video_name = result ,video_path = f"{base_dir}/output_video.mp4")
    session = Session(bind=engine)
    session.add(new_video)
    session.commit()
    session.refresh(new_video)
    try:
        respose = send_email(receiver_email=receiver_email,user_name=username,video_link=new_video)
    except smtplib.SMTPServerDisconnected as er:
        error = db_models.errors(error_code = er.errno , error_message = f" 'SMTPServerDisconnected' {er}",receiver_email = receiver_email)
        session.add(error)
        session.commit()
        session.refresh(error)
    except smtplib.SMTPAuthenticationError as er:
        error = db_models.errors(error_code = er.smtp_code , error_message =f" 'SMTPAuthenticationError' {er}",receiver_email = receiver_email)
        session.add(error)
        session.commit()
        session.refresh(error)
    except smtplib.SMTPSenderRefused as er:
        error = db_models.errors(error_code = er.smtp_code , error_message = f"'SMTPSenderRefused' {er}",receiver_email = receiver_email)
        session.add(error)
        session.commit()
        session.refresh(error)
    except smtplib.SMTPResponseException as er:
        error = db_models.errors(error_code = er.smtp_code , error_message = f"'SMTPResponseException' {er}",receiver_email = receiver_email)
        
        session.add(error)
        session.commit()
        session.refresh(error)

    session.close()
    print("Task completed and email sent")

@router.on_event("startup")
async def startup():
    global current_task
    current_task = {"id": None, "queue": []}


@router.get("/download_video/{file_id}",status_code=status.HTTP_200_OK)
async def download_video(file_id: str, db: Session = Depends(get_db)):
    
    video = db.query(db_models.reid_video).filter(db_models.reid_video.video_name == file_id).first()
    print(video)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid Video ID")
    video_path = video.video_path
    return FileResponse(path=video_path, media_type='application/octet-stream', filename='video.mp4')



@router.get("/history",status_code=status.HTTP_200_OK)
async def video_history( db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):
    current_user_email = form_data.email
    return videoController.history(db=db, current_user_email=current_user_email)