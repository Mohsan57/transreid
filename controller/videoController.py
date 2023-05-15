import os
from datetime import datetime
from fastapi import status, HTTPException
import shutil
from video_preprocessing import video_preprocessing
from object_detection.detect import detect
from transreid.reid import REID
from make_reid_video import Make_ReID_Video
import torch
import random

import setting

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
        


def reduce_frame(base_dir,video_path,fps):
    video_extension = video_path.split(".")[-1]
    
    # video_path = f"{base_dir}/org_video.{video_extension}"
    output_pth = f"{base_dir}/video.{video_extension}"
    frame_reducer = video_preprocessing(input_video = video_path,output_path = output_pth, target_fps = fps)
    
    frame_reducer.reduce_frames()


    
def object_detection(accuracy,video_path,device,ouptut_folder):
    weight = 'object_detection_models/yolov7.pt'
    if accuracy == 'low':
        weight = 'object_detection_models/yolov7.pt'
    elif accuracy == 'medium':
        weight = 'object_detection_models/yolov7-w6.pt'
    elif accuracy == 'high':
        weight = 'object_detection_models/yolov7-d6.pt'
    with torch.no_grad():
       detect(weights=weight, source=video_path,output_dir=ouptut_folder, device = device, name="person" )
        

def TransReID(device, base_dir, weight,image_extension):
    try:
        reid = REID(device, base_dir, weight,image_extension)
        check = reid.idetification()
        if check:
            return True
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in Re-Identification Algorithm method[videoController.Transreid]")
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in Re-Identification Algorithm method[videoController.Transreid]")

def make_reid_video(base_dir,extention):
    video = Make_ReID_Video(base_dir = base_dir, video_extention=extention)
    is_video_make = video.make_video()
    return is_video_make

import string
def get_random_str():
    random_source = string.ascii_letters + string.digits
    # select 1 lowercase
    str1 = random.choice(string.ascii_lowercase)
    # select 1 uppercase
    str1 += random.choice(string.ascii_uppercase)
    # select 1 digit
    str1 += random.choice(string.digits)
    # select 1 special symbol

    # generate other characters
    for i in range(40):
        str1 += random.choice(random_source)

    str_list = list(str1)
    # shuffle all characters
    random.SystemRandom().shuffle(str_list)
    str1 = ''.join(str_list)
    return str1

def reid(device,base_dir,video_url,accuracy,image_extension):
            
            video_extension = video_url.split(".")[-1]

            reduce_frame(base_dir=base_dir, video_path=video_url, fps=setting.VIDEO_CONVERT_FPS)
            video_path_object_detect = f"{base_dir}/video.{video_extension}"
            output_path_object_detect = f"{base_dir}"
            object_detection(accuracy=accuracy, video_path=video_path_object_detect,ouptut_folder=output_path_object_detect,device=device)
            reid_weight = f'trans_reid_models/{setting.TRANSREID_MODEL_NAME}'
            TransReID(device=device,base_dir=base_dir,weight=reid_weight,image_extension=image_extension)

            is_done = make_reid_video(base_dir=base_dir,extention=video_extension)
            
            try:
                shutil.rmtree(f"{base_dir}/identified_people")
                shutil.rmtree(f"{base_dir}/person")
            except shutil.Error as e:
                print("Error in Removing files: "+e)
           
            result_str = get_random_str()
            
            return result_str



    
