from moviepy.video.io.VideoFileClip import VideoFileClip

class video_preprocessing:
    def __init__(self, input_video,output_path,target_fps):
        self.input_video = input_video
        self.output_path = output_path
        self.target_fps = target_fps

    def reduce_frames(self):
        clip = VideoFileClip(self.input_video)

        # get the current fps of the video
        current_fps = clip.fps

        # calculate the frame factor (how many frames to drop)
        frame_factor = current_fps // self.target_fps

        # set the new fps and duration of the video
        new_fps = current_fps / frame_factor
        new_duration = clip.duration

        # reduce the fps by dropping some frames
        clip = clip.set_fps(new_fps)

        # shorten the video duration
        clip = clip.subclip(0, new_duration)

        # save the output video file
        clip.write_videofile(self.output_path, codec='libx264')