from datetime import datetime
import os
import shutil
from fastapi import HTTPException, status
import string
import random
import torch
import numpy as np

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


def upload_video( base_dir ,video, target_image):
                video_extension = video.filename.split(".")[-1]
                image_extension = target_image.filename.split(".")[-1]
                try:
                    with open(f"{base_dir}/org_video.{video_extension}", "wb") as buffer:
                        shutil.copyfileobj(video.file, buffer)
                    with open(f"{base_dir}/target_image.{image_extension}", "wb") as buffer:
                        shutil.copyfileobj(target_image.file, buffer)    
                    return {"video_extension":video_extension,"image_extension":image_extension}
                
                except shutil.ExecError as err:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File Uploading Error\n{err}")

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

def dir_info_file(base_dir,accuracy):
        now = datetime.now()
        today = now.strftime("%d/%m/%Y %H:%M:%S")
        directory_info = open(f"{base_dir}/info.txt",mode="w")
        directory_info.write(f"created at: {today}\n")
        directory_info.write(f"accuracy: {accuracy}")
        directory_info.close()
        
def handler(func, path, exc_info):
    print("shutill remove tree handler")
    print(exc_info)
    

def xywh2xyxy(x):
    # Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2] where xy1=top-left, xy2=bottom-right
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[..., 0] = x[..., 0] - x[..., 2] / 2  # top left x
    y[..., 1] = x[..., 1] - x[..., 3] / 2  # top left y
    y[..., 2] = x[..., 0] + x[..., 2] / 2  # bottom right x
    y[..., 3] = x[..., 1] + x[..., 3] / 2  # bottom right y
    return y
