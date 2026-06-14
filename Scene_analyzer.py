import cv2
import os
from scenedetect import open_video, SceneManager # PySceneDetect - finds the cuts
from scenedetect.detectors import ContentDetector # the algorithm that detects cuts

def find_scenes(video_path):
    video= open_video(video_path)
    scene_manager= SceneManager()
    # ContentDetector is the actual algorithm doing the work.
    # threshold=27 means: if two frames differ by more than 40 (on a 0-255 scale), we will call it a cut
    scene_manager.add_detector(ContentDetector(threshold= 45))
    scene_manager.detect_scenes(video)
    # get_scene_list() gives us a list of (start_time, end_time) pairs
    # e.g. [(00:00:00, 00:00:03), (00:00:03, 00:00:07), ...]
    scene_list= scene_manager.get_scene_list()
    print(f"found {len(scene_list)} scenes in the video...")
    return scene_list

def extract_keyframes(video_path, scene_list, output_folder= "Keyframes"): #For each scene, pulls out ONE representative frame (image) to analyze.
    os.makedirs(output_folder, exist_ok= True)
    cap= cv2.VideoCapture(video_path)
    keyframe_paths= [] #collect the file path of each saved frame here
    for i, scene in enumerate(scene_list): # gives i and scene
         # scene[0] is the start timecode. .get_frames() converts it to a frame number.
         start_frame= scene[0].get_frames()
         cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame) # Tell OpenCV: jump to this frame number in the video
         ret, frame= cap.read()
         # ret = True if reading worked, frame = the image as a numpy array
         if ret:
             # Build a filename like "keyframes/scene_001.jpg"
             frame_path= os.path.join(output_folder, f"scene_{str(i+1).zfill(3)}.jpg")
             cv2.imwrite(frame_path, frame) # save the frame as jpeg file 
             keyframe_paths.append(frame_path)
             print(f"saved keyframe for scene_{i+1}: {frame_path}")

    cap.release()
    print(f"\nExtracted {len(keyframe_paths)} keyframes total.")
    return keyframe_paths




