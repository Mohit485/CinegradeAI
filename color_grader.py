import os
import cv2
import numpy as np
import subprocess
# This dict lives here so you only ever edit it in one place
lut_files = {
    "dark_somber"        : "dark_somber.cube",
    "hard_boost"         : "hard_boost.cube",
    "long_beach_morning" : "long_beach_morning.cube",
    "lush_green"         : "lush_green.cube",
    "magic_hour"         : "magic_hour.cube",
    "natural_boost"      : "natural_boost.cube",
    "orange_and_blue"    : "orange_and_blue.cube",
    "soft_bw"            : "soft_bw.cube",
    "waves"              : "waves.cube",
    "blue_architecture"  : "blue_architecture.cube",
    "blue_hour"          : "blue_hour.cube",
    "cold_chrome"        : "cold_chrome.cube",
    "crisp_autumn"       : "crisp_autumn.cube",
}
 
def load_lut(lut_path):
    try: 
        lut_size= None
        lut_data=[]
        with open(lut_path, "r") as f:
            for line in f:
                line= line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("LUT_3D_SIZE"):
                    lut_size= int(line.split()[-1])
                    continue
                if line[0].isalpha():
                    continue
                values= list(map(float, line.split()))
                if len(values)== 3:
                    lut_data.append(values)

        if lut_size is None or not lut_data:
            return None
        lut_array= np.array(lut_data, dtype= np.float32).reshape(
            lut_size, lut_size, lut_size, 3
        )
        return lut_array 
    except Exception as e:
        print(f"could not load lut {lut_path}: {e}")
        return None

def load_lut_lib(lut_folder= "lut"):
    
    lut_lib= {}
    for style_name, file_name in lut_files.items():
        file_path= os.path.join(lut_folder, file_name)

        if os.path.exists(file_path):
            lut_array= load_lut(file_path)
            lut_lib[style_name]= lut_array
            status = "loaded" if lut_array is not None else "failed to parse"
            print(f"  LUT '{style_name}': {status}")
        else:
            lut_lib[style_name] = None
            print(f"  LUT '{style_name}': file not found — will skip for this style")
    return lut_lib
        
def apply_lut2frame(frame, lut_array):
    lut_size= lut_array.shape[0]
    #convert 0-255 values into 0.0-1.0  values
    frame_float= frame.astype(np.float32)/ 255.0
    # OpenCV stores images as BGR — split into separate channels
    b,g,r= cv2.split(frame_float)
    # Scale 0.0-1.0 values into LUT grid indices (0 to lut_size-1)
    # np.clip ensures no index goes out of bounds
    r_idx= np.clip((r* (lut_size-1)).astype(int), 0, (lut_size-1))
    g_idx= np.clip((g* (lut_size-1)).astype(int), 0,(lut_size-1))
    b_idx= np.clip((b*(lut_size-1-1)).astype(int), 0, (lut_size-1))
    # Look up the mapped RGB values in the LUT 3D grid
    mapped= lut_array[b_idx, g_idx, r_idx]
    # flip RGB → BGR, scale to 0–255, stay float32
    return (mapped[:, :, ::-1] * 255.0).astype(np.float32)

def apply_brightness_contrast(frame, brightness, contrast):

    result = frame + float(brightness)
    # ── Step 2: Contrast ──────────────
    alpha    = 1.0 + (contrast / 100.0)
    result   = (result - 128.0) * alpha + 128.0
    return np.clip(result, 0.0, 255.0)
     

def apply_saturation(frame, saturation_scale):
    #We convert the image from BGR (Blue-Green-Red, how OpenCV stores images) to HSV (Hue-Saturation-Value). #
    # In HSV, saturation is its own channel. We just multiply that channel by our scale factor, then convert back.
    hsv= cv2.cvtColor(np.clip(frame,0.0,255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1]*= saturation_scale
    hsv[:,:,1]= np.clip(hsv[:,:,1],0,255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
    

def apply_temperature(frame, temp):
    if temp== "warm":
        frame[:,:,2]*= 1.08 # red channel multiply by 1.08= +8%
        frame[:,:,0]*= 0.92 #blue channel multiply by 0.92= -8%

    elif temp== "cool":
        frame[:,:,2]*= 0.92
        frame[:,:,0]*= 1.08

    #neutral dont change anything
    return np.clip(frame, 0.0,255.0)
    

def grade_frame(frame, analysis, lut_lib):
    #Applies ALL the adjustments from Gemini's JSON to a single frame.
    adjustments= analysis.get("adjustments", {})
    result = frame.astype(np.float32)

    #brightness and contrast
    # .get() with a default value means: use this value if the key doesn't exist
    brightness= adjustments.get("brightness", 0)
    contrast= adjustments.get("contrast", 0)
    graded= apply_brightness_contrast(result, brightness, contrast)
    graded  = graded.clip(0, 255).astype(np.uint8)
    #saturation
    saturation= adjustments.get("saturation", 1.0)
    graded= apply_saturation(graded, saturation)

    # color temperature
    color_temp= adjustments.get("color_temp", "neutral")
    graded= apply_temperature(graded, color_temp)

    # Step 4: LUT — applied last so it grades the already-corrected image
    lut_style = adjustments.get("lut", "none")
    if lut_style and lut_style != "none" and lut_style in lut_lib:
        lut_array = lut_lib[lut_style]
        if lut_array is not None:
            graded = apply_lut2frame(graded, lut_array)
 
    return np.clip(graded, 0.0, 255.0).astype(np.uint8)


def build_scene_map(scene_list, all_analyses):
    #Builds a list of (start_frame, end_frame, analysis_dict) tuples using the ACTUAL scene boundaries from PySceneDetect.
    scene_map= []
    for i, scene, in enumerate(scene_list):
        # .get_frames() converts a timecode to an actual frame number (integer)
        start_frame = scene[0].get_frames()
        end_frame   = scene[1].get_frames()
        # Match this scene to its analysis dict by index
        if i < len(all_analyses):
            analysis = all_analyses[i]
        else:
            analysis = all_analyses[-1] if all_analyses else {}
 
        scene_map.append((start_frame, end_frame, analysis))
 
    return scene_map

def get_analysis(frame_number, scene_map):
    for start, end, analysis in scene_map:
        if start<= frame_number< end:
            return analysis
        
    if scene_map:
        return scene_map[-1][2]
    else:
        return {}




def apply_grading2video(video_path, scene_list, analysis_results, output_path= "output_graded.mp4", lut_folder= "lut"):
    #Processes the entire video — reads every frame, checks which scene it belongs
    #to, applies that scene's grading, and writes the result to a new video file.
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    lut_library = load_lut_lib(lut_folder)
    scene_map = build_scene_map(scene_list, analysis_results)

    cap= cv2.VideoCapture(video_path)
    fps= cap.get(cv2.CAP_PROP_FPS)
    width= int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height= int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames= int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"/n VIDEO INFO: {width} x {height} @ {fps}, {total_frames} frames total")

    # VideoWriter lets us write frames to a new video file
    # cv2.VideoWriter_fourcc is the codec (video compression format)
    fourcc= cv2.VideoWriter_fourcc(*"mp4v")
    out= cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_number= 0
    # loop through every single frame of video 
    while True:
        ret, frame= cap.read()
        #ret becomes false when we reach end of this video
        if not ret:
            break
        adjustments= get_analysis(frame_number, scene_map) # Look up what adjustments apply to this frame number
        #apply grading
        if adjustments:
            graded_frame= grade_frame(frame, adjustments, lut_library)
        else:
            graded_frame= frame

        out.write(graded_frame)# Write this frame to the output video
        frame_number+= 1

        if frame_number%100== 0:
            percent= int((frame_number/ total_frames)*100)
            print(f"  Progress: {percent}%  ({frame_number}/{total_frames} frames)")

    cap.release()
    out.release()
    print(f"graded video saved to {output_path}")

    return output_path


