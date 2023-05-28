from fastapi import status, HTTPException
import shutil
from video_preprocessing import video_preprocessing
from object_detection.detect import ObjectDetection
from transreid.reid import REID
from make_reid_video import Make_ReID_Video
from file_operations import get_random_str, handler
import torch
import setting

class VideoController():
    def __init__(self, base_dir ,accuracy, video_extension, image_extension):
        self.base_dir = base_dir
        self.accuracy =accuracy
        self.object_detec_weight = 'object_detection_models/yolov7.pt'
        if self.accuracy == 'low':
           self.object_detec_weight = 'object_detection_models/yolov7.pt'
        elif self.accuracy == 'medium':
            self.object_detec_weight = 'object_detection_models/yolov7-w6.pt'
        elif self.accuracy == 'high':
            self.object_detec_weight = 'object_detection_models/yolov7-d6.pt'
        self.video_extension = video_extension
        self.image_extension = image_extension
        self.video_path = f"{self.base_dir}/org_video.{self.video_extension}"
        
        
    
    def __del__(self):
        try:
            shutil.rmtree(f"{self.base_dir}/identified_people", onerror=handler)
            shutil.rmtree(f"{self.base_dir}/person",onerror=handler)
        except shutil.Error as e:
            print("Error in Removing files: "+e)
        

    def reduce_frame(self):
        output_pth = f"{self.base_dir}/video.{self.video_extension}"
        frame_reducer = video_preprocessing(input_video = self.video_path,output_path = output_pth, target_fps = setting.VIDEO_CONVERT_FPS)
        frame_reducer.reduce_frames()
        
    def object_detection(self):
        detection = ObjectDetection(weights=self.object_detec_weight, output_dir=self.base_dir)
        video_url = f"{self.base_dir}/video.{self.video_extension}"
        detection.detect(source=video_url)

    def TransReID(self):
        try:
            _reid = REID(base_dir=self.base_dir,image_extension=self.image_extension)
            check = _reid.idetification()
            if check:
                return True
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in Re-Identification Algorithm method[videoController.Transreid]")
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in Re-Identification Algorithm method[videoController.Transreid]")

    def make_reid_video(self):
        video = Make_ReID_Video(base_dir = self.base_dir, video_extention=self.video_extension)
        is_video_make = video.make_video()
        return is_video_make
    
    def reid(self):
        self.reduce_frame()
        self.object_detection()
        self.TransReID()
        is_done = self.make_reid_video()
        result_str = get_random_str()
                
        return result_str
