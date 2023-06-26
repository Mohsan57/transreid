from transreid.reid import REID

reid = REID(base_dir='users/1/video1',image_extension='png')
reid.idetification()

# from make_reid_video import Make_ReID_Video
# video = Make_ReID_Video(base_dir = "users/1/video1", video_extention="mp4")
# is_video_make = video.make_video()