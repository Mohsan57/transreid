import os
from datetime import datetime
import db_models
from fastapi import status, HTTPException
import shutil
from video_preprocessing import video_preprocessing
from object_detection.detect import detect
from transreid.reid import REID
from make_reid_video import Make_ReID_Video
import torch
import pathlib
import glob

def make_dir(user_id):
    base_dir = f"users/{user_id}/"
    prefix = "video"
    max_num = 0

    # Find the highest numbered directory
    for directory in os.listdir(base_dir):
        if directory.startswith(prefix):
            try:
                num = int(directory[len(prefix):])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass

    # Create a new directory with the next number in the series
    new_dir_name = f"{prefix}{max_num + 1}"
    os.mkdir(os.path.join(base_dir, new_dir_name))
    return new_dir_name


def dir_info_file(base_dir,accuracy):
    now = datetime.now()
    today = now.strftime("%d/%m/%Y %H:%M:%S")

    directory_info = open(f"{base_dir}/info.txt",mode="w")
    directory_info.write(f"created at: {today}\n")
    directory_info.write(f"accuracy: {accuracy}")
    directory_info.close()

def upload_video(base_dir,video,target_image):
    target_image_type = target_image.content_type
    video_type = video.content_type

    if target_image_type.startswith("image") and video_type.startswith("video"):
        if video.size <= 60000000:
            video_extension = video.filename.split(".")[-1]
            image_extension = target_image.filename.split(".")[-1]
            try:
                with open(f"{base_dir}/org_video.{video_extension}", "wb") as buffer:
                    shutil.copyfileobj(video.file, buffer)
                with open(f"{base_dir}/target_image.{image_extension}", "wb") as buffer:
                    shutil.copyfileobj(target_image.file, buffer)    
                return status.HTTP_200_OK
            
            except shutil.ExecError as err:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File Uploading Error\n{err}")
        else:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Video size will not exceed 60MB")
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Please Upload Only Video and Image")


def reduce_frame(base_dir,video,fps):
    video_extension = video.filename.split(".")[-1]
    video_path = f"{base_dir}/org_video.{video_extension}"
    output_pth = f"{base_dir}/video.{video_extension}"
    
    frame_reducer = video_preprocessing(input_video = video_path,output_path = output_pth, target_fps = fps)
    
    frame_reducer.reduce_frames()


    
def object_detection(accuracy,video_path,device,ouptut_folder):
    weight = 'object_detection_models/yolov7.pt'
    if accuracy == 'low':
        weight = 'object_detection_models/yolov7.pt'
    elif accuracy == 'medium':
        weight = 'object_detection_models/yolov7-w6.pt'
    elif accuracy == 'heigh':
        weight = 'object_detection_models/yolov7-d6.pt'
    with torch.no_grad():
       detect(weights=weight, source=video_path,output_dir=ouptut_folder, device = device, name="person" )
        

def TransReID(device, base_dir, weight):
    reid = REID(device, base_dir, weight)
    check = reid.idetification()
    if check:
        return True
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in Re-Identification Algorithm")

def make_reid_video(base_dir,extention):
    video = Make_ReID_Video(base_dir = base_dir, video_extention=extention)
    is_video_make = video.make_video()
    return is_video_make


def detect_using_video(db,device,current_user_email,video,accuracy,target_image):
    target_image_type = target_image.content_type
    video_type = video.content_type
    
    if target_image_type.startswith("image") and video_type.startswith("video"):
        if video.size <= 15000000:
            users = db.query(db_models.User).filter(db_models.User.email == current_user_email).first()
            user_id = users.id
            dir_name = make_dir(user_id=user_id)
            video_extension = video.filename.split(".")[-1]

            base_dir = f'users/{user_id}/{dir_name}'
            dir_info_file(base_dir = base_dir,accuracy=accuracy)
            
            uploaded_status =  upload_video(base_dir=base_dir, video= video, target_image=target_image)
            reduce_frame(base_dir=base_dir, video=video, fps=8)
            video_path_object_detect = f"{base_dir}/video.{video_extension}"
            output_path_object_detect = f"{base_dir}"
            object_detection(accuracy=accuracy, video_path=video_path_object_detect,ouptut_folder=output_path_object_detect,device=device)
            reid_weight = 'trans_reid_models/transformer_120.pth'
            TransReID(device=device,base_dir=base_dir,weight=reid_weight)

            is_done = make_reid_video(base_dir=base_dir,extention=video_extension)
            video.close()
            try:
                shutil.rmtree(f"{base_dir}/identified_people")
                shutil.rmtree(f"{base_dir}/person")
            except shutil.Error as e:
                print("Error in Removing files: "+e)
            if is_done:
                return f"{base_dir}/output_video.mp4"
            else:
                HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Server Error durin Making Video")
        else:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Video size will not exceed 15MB")
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Please Upload Only Video and Image")
    

def history(db,current_user_email):
    users = db.query(db_models.User).filter(db_models.User.email == current_user_email).first()
    user_id = users.id
    user_dirs = f"users/{user_id}/"
    history = []
    for directory in os.listdir(user_dirs):
        created_date = ""
        accuracy = ""
        files = []
        files.append(glob.glob(f"{user_dirs}/{directory}/*"))
        for files_path in files:
            list = []
            for file_path in files_path:
                file = file_path.split("\\")[-1]
                if(file == "info.txt"):
                    with open(file_path,mode="r") as f:
                        created_date = f.readline()
                        accuracy = f.readline()
                        l = {"created at":created_date.split(": ")[1]}
                        list.append(l)
                        l = {"accuracy":accuracy.split(": ")[1]}
                        list.append(l)
                if "video" in file:
                    l = {"input video": file_path}
                    list.append(l)
                if "target_image" in file:
                    l = {"target images": file_path}
                    list.append(l)
                if "output_video" in file:
                    l = {"output video": file_path}
                    list.append(l)
            history.append(list)
    return history


    
