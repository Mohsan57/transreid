import os
from .model import make_model
import torchvision.transforms as T
import torch
from PIL import Image
import torch.nn as nn
import glob

transform = T.Compose([
    T.Resize((256, 128)),
    T.ToTensor(),
    T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

class REID:
  def __init__(self, device, base_dir, weight):
    self.device = torch.device(device)
    self.base_dir = base_dir
    self.weight = weight
    self.num_classes, self.camera_num, self.view_num = 702,8,1
    self.model = make_model(num_class=self.num_classes, camera_num=self.camera_num, view_num = self.view_num,device = self.device)

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
      try:
        images = []
        images = glob.glob(f"{self.base_dir}/person/crops/person/*.jpg")

        images = sorted(images, key=self.extract_number)
        target = f"{self.base_dir}/target_image.jpg"

        target_image = Image.open(target)
        target_image_to_tensor = transform(target_image).unsqueeze(0)
        target_tensor = self.model(target_image_to_tensor, cam_label=6, view_label=1)

        try:
          os.mkdir(f"{self.base_dir}/identified_people/")
        except:
          print("already exist directory")

        with open(f"{self.base_dir}/identified_people/information.txt", "w") as writefile:
          for image in images:
            open_image = Image.open(image)
            image_tensor = transform(open_image).unsqueeze(0)
            image_tensor = self.model(image_tensor,  cam_label=6, view_label=1)
            similarity = torch.nn.functional.cosine_similarity(target_tensor, image_tensor)
            if(similarity[0]>=0.71):
              print( f" image index {image} cosine is: {str(similarity[0])}")
              str2, str3 = image.split("\\")
              writefile.write(f"{str3}\n")
        
        return True
      except:
         return False


