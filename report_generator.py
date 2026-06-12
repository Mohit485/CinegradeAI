from fpdf import FPDF
import os

def create_report(analysis_result , output_path= "analysis_report.pdf"):
    # Create a new PDF object
    pdf= FPDF(orientation= 'P', unit= 'mm', format= 'A4')
    pdf.add_page()
    pdf.set_font("Arial", "B", 24)
    pdf.ln(40)
    # cell() prints text. Parameters: width, height, text, border, new_line, alignment
    pdf.cell(0, 12, "AI Video Analysis Report", ln=True, align= "C")
    pdf.set_font("Arial", "", 14)
    pdf.set_text_color(120,120,120)
    pdf.ln(5)
    pdf.cell(0,8, f"total scenes analyzed: {len(analysis_result)}", ln= True, align="C")
    pdf.set_text_color(0,0,0)

     # ---- One page per scene ----
    for result in analysis_result:
 
        pdf.add_page()   # each scene gets a fresh page
 
        scene_num = result.get("scene_number", "?")
 
        # --- Scene header ---
        pdf.set_font("Arial", "B", 16)
        pdf.set_fill_color(30, 30, 30)       # dark background
        pdf.set_text_color(255, 255, 255)    # white text on dark background
        # fill=True draws a filled rectangle behind the text
        pdf.cell(0, 10, f"  Scene {scene_num}", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)          # back to black text
        pdf.ln(3)
 
        # --- Keyframe image ---
        image_path = result.get("image_path", "")
        if image_path and os.path.exists(image_path):
            # Add image to PDF. x=10, y=current position, w=190 (full width minus margins)
            # The height is set automatically to maintain aspect ratio
            pdf.image(image_path, x=10, w=190)
            pdf.ln(5)

        # --- Scene description ---
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 7, "Scene Description:", ln=True)
        pdf.set_font("Arial", "", 10)
        # multi_cell() wraps long text automatically — unlike cell() which cuts it off
        description = result.get("scene_description", "No description available.")
        pdf.multi_cell(0, 6, description)
        pdf.ln(3)
 
        # --- Mood ---
        pdf.set_font("Arial", "B", 11)
        pdf.cell(40, 7, "Mood Detected:", ln=False)   # ln=False means stay on same line
        pdf.set_font("Arial", "", 11)
        mood = result.get("mood", "unknown").upper()
        pdf.cell(0, 7, mood, ln=True)
        pdf.ln(2)
        # --- Issues ---
        issues = result.get("issues", [])
        if issues:
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 7, "Issues Found:", ln=True)
            pdf.set_font("Arial", "", 10)
            for issue in issues:
                # chr(8226) is the bullet point character •
                pdf.cell(5, 6, "", ln=False)         # small indent
                pdf.cell(0, 6, f"{issue}", ln=True)
            pdf.ln(2)
 
        # --- Director's note ---
        note = result.get("director_note", "")
        if note:
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 7, "Director's Note:", ln=True)
            pdf.set_font("Arial", "I", 10)   # Italic for the creative note
            pdf.set_text_color(60, 60, 150)  # a slightly blue color
            pdf.multi_cell(0, 6, f'"{note}"')
            pdf.set_text_color(0, 0, 0)
            pdf.ln(3)

        # --- Adjustments applied ---
        adjustments = result.get("adjustments", {})
        if adjustments:
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 7, "Color Grading Applied:", ln=True)
            pdf.set_font("Arial", "", 10)
 
            brightness = adjustments.get("brightness", 0)
            contrast = adjustments.get("contrast", 0)
            saturation = adjustments.get("saturation", 1.0)
            color_temp = adjustments.get("color_temp", "neutral")
            lut = adjustments.get("lut", "none")                              # reads lut from Gemini JSON


            # Format each adjustment on its own line
            pdf.cell(0, 6, f"  Brightness: {'+' if brightness > 0 else ''}{brightness}", ln=True)
            pdf.cell(0, 6, f"  Contrast:   {'+' if contrast > 0 else ''}{contrast}", ln=True)
            pdf.cell(0, 6, f"  Saturation: {saturation}x", ln=True)
            pdf.cell(0, 6, f"  Color Temp: {color_temp.capitalize()}", ln=True)
            pdf.cell(0, 6, f"  LUT Style:  {lut.replace('_', ' ').title()}", ln=True)  
    # Save the PDF to disk
    pdf.output(output_path)
 
    print(f"PDF report saved to: {output_path}")
    return output_path
    
