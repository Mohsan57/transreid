import sys
sys.path.insert(0, './object_detection')
from pathlib import Path
import torch
import torch.backends.cudnn as cudnn
from .models.experimental import attempt_load
from .utils.datasets import LoadStreams, LoadImages
from .utils.general import check_img_size, \
                check_imshow, non_max_suppression, \
                scale_coords, xyxy2xywh, set_logging, \
                increment_path,  save_one_box
from .utils.torch_utils import select_device
from setting import DEVICE


class ObjectDetection():
    def __init__(self,weights,output_dir):
        self.weights = weights
        self.save_txt = True
        self.imgsz = 640
        self.output_dir = output_dir
        self.name = 'person' 
         # checkkkkkk 
        self.save_dir = Path(increment_path(Path(self.output_dir) / self.name, exist_ok=False))  # increment run
        (self.save_dir / 'labels' if self.save_txt else self.save_dir).mkdir(parents=True, exist_ok=True)  # make dir

        # Initialize
        set_logging()
        self.device = select_device(DEVICE)
        self.half = self.device.type != 'cpu'  # half precision only supported on CUDA
        # Load model
        
        self.model = attempt_load(self.weights, map_location=self.device)  # load FP32 model
        self.stride = int(self.model.stride.max())  # model stride
        self.imgsz = check_img_size(self.imgsz, s=self.stride)  # check img_size
        
        if self.half:
            print("gpu")
            self.model.half()  # to FP16
        
         # Get names and colors
        self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names
        # Run inference
        if self.device.type != 'cpu':
            self.model(torch.zeros(1, 3, self,self.imgsz, self.imgsz).to(self.device).type_as(next(self.model.parameters())))  # run once
        self.old_img_w = self.old_img_h = self.imgsz
        self.old_img_b = 1
        
    def __del__(self):
        del self.model, self.half, self.save_dir
    
    def detect(self, source):
        augment = False
        dataset = LoadImages(source, img_size=self.imgsz, stride=self.stride)
        
        for path, img, im0s, vid_cap in dataset:
            img = torch.from_numpy(img).to(self.device)
            img = img.half() if self.half else img.float()  # uint8 to fp16/32
            img /= 255.0  # 0 - 255 to 0.0 - 1.0
            if img.ndimension() == 3:
                img = img.unsqueeze(0)

            # Warmup
            if self.device.type != 'cpu' and (self.old_img_b != img.shape[0] or self.old_img_h != img.shape[2] or self.old_img_w != img.shape[3]):
                self.old_img_b = img.shape[0]
                self.old_img_h = img.shape[2]
                self.old_img_w = img.shape[3]
                for i in range(3):
                    self.model(img, augment=augment)[0]

            # Inference
            with torch.no_grad():
                pred = self.model(img, augment=augment)[0]
            
            conf_thres = 0.25
            iou_thres = 0.45
            classes = 0
            agnostic_nms = False
            save_conf = False
            # Apply NMS
            pred = non_max_suppression(pred, conf_thres,iou_thres, classes=classes, agnostic=agnostic_nms)

            # Process detections
            for i, det in enumerate(pred):  # detections per image
                
                p, s, im0, frame = path, '', im0s, getattr(dataset, 'frame', 0)
                
                p = Path(p)  # to Path
                save_path = str(self.save_dir / p.name)  # img.jpg
                txt_path = str(self.save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # img.txt
                gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
                if len(det):
                    # Rescale boxes from img_size to im0 size
                    det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                    # Print results
                    for c in det[:, -1].unique():
                        n = (det[:, -1] == c).sum()  # detections per class
                        s += f"{n} {self.names[int(c)]}{'s' * (n > 1)}, "  # add to string

                    # Write results
                    for *xyxy, conf, cls in reversed(det):
                    
                        if self.save_txt:  # Write to file
                            name = save_one_box(xyxy=xyxy, im= im0, file=self.save_dir / 'crops' / self.names[int(c)] / f'{p.stem}.jpg', square=False, BGR=True, save=True)
                            file_name_strip = name.split("\\")
                            file_name = file_name_strip[-1]
                            xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                            line = (cls, *xywh, conf) if save_conf else (cls, *xywh)  # label format
                            with open(txt_path + '.txt', 'a') as f:
                                f.write(file_name+(' %g ' * len(line)).rstrip() % line + '\n')

