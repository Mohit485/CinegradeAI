import gradio as gr
from main import run_pipeline

def process_video(video_file):
    if video_file is None:
        return None, None, "Please Upload a File", None
    try:
        results= run_pipeline(video_file, output_dir="gradio_output")
        if results is None:
            return None, None, "Could not detect scenes in this video", None
        lines= []
        for scene in results["analysis"]:
            adj= scene.get("adjustments", {})
            lines.append(f"SCENE {scene.get('scene_number', '?')}")
            lines.append(f"Mood: {scene.get('mood', '')}")
            lines.append(f"Description: {scene.get('scene_description', '')}")
            lines.append(f"Director: {scene.get('director_note', '')}")
            lines.append(f"Issues: {', '.join(scene.get('issues', []))}")
            lines.append(f"Brightness: {adj.get('brightness', 0)}")
            lines.append(f"Contrast: {adj.get('contrast', 0)}")
            lines.append(f"Saturation: {adj.get('saturation', 1.0)}")
            lines.append(f"Color Temperature: {adj.get('color_temp', 'neutral')}")
            lines.append(f"LUT: {adj.get('lut', 'none')}")
            lines.append("")
        summary= "\n".join(lines)
        return results["graded_video"], results["report"], summary, video_file
    except Exception as e:
        error= f"Something went wrong: \n{str(e)}\n\nCheck that GOOGLE_API_KEY is set."
        return None, None, error, None
    


# Build The UI
with gr.Blocks(title= "Cinegrade") as app:
    gr.Markdown("# Cinegrader: AI Video Scene Analyzer and Color Grader")
    gr.Markdown("Upload a video. Gemini analyzes each scene and applies AI color grading.")
    video_input= gr.Video(label= "Upload your Video")
    analyze_btn= gr.Button("Analyze & Grade", variant= "primary")
    gr.Markdown("## Results")
    # Two videos side by side for before/after comparison
    with gr.Row():
        original_video= gr.Video(label="Original Video")
        graded_video= gr.Video(label="AI Graded")
    # Analysis text and PDF download side by side below the videos
    with gr.Row():
        analysis_text= gr.Textbox(label="Scene Analysis", lines=20, interactive= False)
        pdf_out= gr.File(label= "Download PDF File")
    analyze_btn.click(
        fn= process_video,
        inputs=[video_input],
        outputs=[graded_video, pdf_out, analysis_text, original_video]
    )  
if __name__== "__main__": 
    app.launch(share= True)




            


            