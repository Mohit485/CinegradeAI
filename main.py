import os
import json
from Scene_analyzer import find_scenes, extract_keyframes
from color_grader import apply_grading2video
from frame_anlyzer import setup_gemini, analyze_all_frames
from report_generator import create_report
def run_pipeline(video_path, output_dir= "dir"): 
    '''The pipeline steps in order:
    1. Find all scene cuts in the video
    2. Extract one keyframe image per scene
    3. Send each keyframe to Gemini for analysis
    4. Apply the suggested color grading to the full video
    5. Generate a PDF report'''
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"file not found{video_path}")
    print("=" * 50)
    print("AI VIDEO SCENE ANALYZER")
    print("=" * 50)
    print(f"Input video: {video_path}")
    print(f"Output folder: {output_dir}")
    print()

    #os.makedirs("output_dir", exist_ok= True)
    #define where each output file will be saved
    keyframe_dir= os.path.join(output_dir, "keyframes")
    graded_path= os.path.join(output_dir, "graded_video.mp4")
    report_path= os.path.join(output_dir, "analysis_report.pdf")
    json_path= os.path.join(output_dir, "analysis_data.json")

    os.makedirs(output_dir, exist_ok=True)

    print("STEP=1: detecting scenes")
    scene_list= find_scenes(video_path)
    if not scene_list:
        print(f"Warning ! No scenes Detected, The video might be a single uncut shot.")
        print("Treating the whole video as one scene.")
        return None
    print("STEP-2: Extracting Keyframes")
    keyframe_paths= extract_keyframes(video_path, scene_list, output_folder= keyframe_dir)

    print("STEP-3: Analyzing frames with Gemini AI")
    model= setup_gemini()
    #analyze all frames
    analysis_results= analyze_all_frames(model, keyframe_paths)
    # Save the raw analysis data as a JSON file
    with open(json_path, "w") as f:
        json.dump(analysis_results, f, indent= 2)
    print(f"Analysis data saved to {json_path}")

    #Apply color grading to video
    print("Applying Color Grading to Video")
    graded_path= apply_grading2video(
        video_path=video_path, scene_list= scene_list, analysis_results=analysis_results, output_path= graded_path)

    print("  Merging original audio into graded video...")
    final_path = graded_path.replace(".mp4", "_final.mp4")
    os.system(
        f'ffmpeg -y -i "{graded_path}" -i "{video_path}" ' +
        f'-map 0:v:0 -map 1:a:0 -c copy -shortest "{final_path}" -loglevel error'
    )
    if os.path.exists(final_path):
        graded_path = final_path
        print(f"  Audio merged: {final_path}")
    else:
        print("  FFmpeg not found — output has no audio. Install FFmpeg to preserve audio.")
 
    #generating Report PDF
    print("Report File Generation")
    report= create_report(analysis_results, output_path= report_path)

    print("Pipeline Comeplete")
    print(f"  Graded video:    {graded_path}")
    print(f"  PDF report:      {report}")
    print(f"  Raw JSON data:   {json_path}")
    print(f"  Keyframes:       {keyframe_dir}/")

    return{
        "graded_video": graded_path,
        "report": report,
        "json_data": json_path,
        "keyframe_dir": keyframe_dir,
        "analysis" : analysis_results
    }
 # This block only runs if you execute main.py directly from the terminal
if __name__== "__main__":
    import sys
    # sys.argv is a list of command line arguments
    # sys.argv[0] = "main.py" (the script name)
    # sys.argv[1] = the video path you type after the script name
    if len(sys.argv)<2:
        print("Usage: python main.py path/to/your/video.mp4")
        print("Example: python main.py sample.mp4")
    video_file= sys.argv[1]
    run_pipeline(video_file)
