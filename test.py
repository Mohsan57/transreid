from transreid.reid import REID
from make_reid_video import Make_ReID_Video
import re
# reid = REID("users/1/video9","png")
# reid.idetification()

video = Make_ReID_Video("users/1/video9","mp4")
video.make_video()  

# detect_people = ['video.jpg','video5.jpg','video9000.jpg']
# pattern = r'\d+'
# detect_people = sorted(detect_people, key=lambda x: int(re.findall(pattern, x)[0]) if re.findall(pattern, x) else float('inf'))
# if 'video.jpg' in detect_people:
#     detect_people.pop()
#     detect_people.insert(0,'video.jpg')
# print(detect_people)
