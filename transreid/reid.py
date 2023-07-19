import os
from .model import make_model
import torchvision.transforms as T
import torch
from PIL import Image
import torch.nn as nn
import glob
import setting
import re
import cv2
transform = T.Compose([
    T.Resize((256, 128)),
    T.ToTensor(),
    T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

class REID:
  def __init__(self, base_dir,image_extension):
    self.image_extension = image_extension
    self.device = None
    if setting.DEVICE == 'cuda':
       self.device = 'cuda'
    else:
      self.device = torch.device(setting.DEVICE)
    self.base_dir = base_dir
    self.weight = f"trans_reid_models/{setting.TRANSREID_MODEL_NAME}"
    self.num_classes, self.camera_num, self.view_num = 702,8,1
    self.model = None
    self.model = make_model(num_class=self.num_classes, camera_num=self.camera_num, view_num = self.view_num,device=self.device)
    
    self.model.load_param(self.weight)
    self.model = nn.DataParallel(self.model)
    self.model.to(self.device)
    self.model.eval()

    target = f"{self.base_dir}/target_image.{self.image_extension }"
    target_image = Image.open(f"{target}").convert('RGB')
        
    target_image_to_tensor = transform(target_image).unsqueeze(0)
        
    self.target_tensor = self.model(target_image_to_tensor, cam_label=6, view_label=1)
     
  
  def reload_model(self):
    print("reload ReID model")
    self.model = make_model(num_class=self.num_classes, camera_num=self.camera_num, view_num = self.view_num,device=self.device)
    
    self.model.load_param(self.weight)
    self.model = nn.DataParallel(self.model)
    self.model.to(self.device)
    self.model.eval()
    
  def extract_number(self,filename):
      try:
          return int(filename.split('/')[-1][5:-4])
      except (ValueError, IndexError):
          # return a large number if the filename doesn't contain a valid number
          return float('inf')
  def idetification(self):
      print("start identification")
      try:
        images = []
        images = glob.glob(f"{self.base_dir}/person/crops/person/*.jpg")
        
        images = sorted(images, key=self.extract_number)
        target = f"{self.base_dir}/target_image.{self.image_extension }"
        
        # target_image = Image.open(target).convert('RGB')
        
        # target_image_to_tensor = transform(target_image).unsqueeze(0)
        # if self.model is None:
        #   self.reload_model()

        # target_tensor = self.model(target_image_to_tensor, cam_label=6, view_label=1)
        try:
          os.mkdir(f"{self.base_dir}/identified_people/")
        except:
          print("already exist directory")
        try:
          writefile = open(f"{self.base_dir}/identified_people/information.txt", "w")
          
          if len(images) != 0:
            for image in images:
              open_image = Image.open(image).convert('RGB')
              image_tensor = transform(open_image).unsqueeze(0)
              image_tensor = self.model(image_tensor,  cam_label=6, view_label=1)
              similarity = torch.nn.functional.cosine_similarity(self.target_tensor, image_tensor)
              if(similarity[0]>=setting.TRANSREID_ACCURACY_MATCH):
                print( f" image index {image} cosine is: {str(similarity[0])}")
                value = round(similarity.item(),2)
                
                file_name = os.path.basename(image)
                  
                # str2 = image.split("/")
                writefile.write(f"{file_name},{value}\n")
                if(float(value) >= 0.95):
                    files = os.listdir(self.base_dir)
                    for file in files:
                        if file.startswith("target_image"):
                            os.remove(f"{self.base_dir}/{file}")
                    #crop image
                    open_image.save(f"{self.base_dir}/target_image.jpg")
                    # cv2.imwrite(f"{self.base_dir}/target_image.jpg", open_image) 

          writefile.close()
        except Exception as e:
          print("error in writing file")
          print(e)
        return True
      except:
         return False


