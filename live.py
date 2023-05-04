import cv2
import time
from object_detection import detect
import torch
# IP address and credentials for the CCTV camera
ip_address = "192.168.1.2:8080"
username = "admin"
password = "admin"

# URL for the camera's video feed
url = f"http://{username}:{password}@{ip_address}/video"
with torch.no_grad():
    detect.detect(source = url, weights= "object_detection_models/yolov7.pt",output_dir="users/test/")
# def detect(source,weights,output_dir)

# body = cv2.CascadeClassifier('test/haarcascade_frontalface_alt2.xml')

# # # Open the video stream using OpenCV
# cap = cv2.VideoCapture(url)




# fps = cap.get(cv2.CAP_PROP_FPS)
# frame_rate = 10
# prev = 0

# print("Frame rate: ", fps)
# # Loop over frames from the video stream
# while True:
#     time_elapsed = time.time() - prev
#     res, frame = cap.read()

#     if time_elapsed > 1./frame_rate:
#         prev = time.time()
#         resize_frame = cv2.resize(frame, (600, 420))
#         # Convert the frame to grayscale
#         gray = cv2.cvtColor(resize_frame, cv2.COLOR_BGR2GRAY)

#         # Detect objects in the grayscale frame
#         objects = body.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

#         # Draw bounding boxes around the detected objects
#         for (x, y, w, h) in objects:
#             cv2.rectangle(resize_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
#         # Display the frame on the screen
#         cv2.imshow('frame', resize_frame)

#         # Wait for a key press and exit if 'q' is pressed
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

# # Release the camera and close the window
# cap.release()
# cv2.destroyAllWindows()