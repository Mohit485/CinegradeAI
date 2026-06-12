# 🎬 CineGrade AI

### AI-powered video scene analysis and color grading pipeline

> Upload any video. CineGrade AI detects every scene cut, analyzes the cinematography of each shot using Gemini Vision, and automatically applies professional color grading — brightness, contrast, saturation, color temperature, and LUT — scene by scene.

![Banner](assets/banner.png)


---

## ✨ What It Does

- 🎞️ Detects every shot cut in a video automatically using **PySceneDetect**
- 🖼️ Extracts one representative keyframe per scene
- 🤖 Sends each keyframe to **Gemini 2.5 Flash Vision** for cinematographic analysis — lighting quality, mood, composition, exposure issues
- 📋 Receives structured grading instructions back as JSON — brightness, contrast, saturation, color temperature, LUT selection
- 🎨 Applies all adjustments **frame by frame** using OpenCV with a full float32 pipeline to prevent flickering
- 🎞️ Applies one of **13 professional `.cube` LUT files** chosen by the AI based on scene mood
- 📄 Exports a **color graded video** and a **PDF report** with keyframe images and director's notes per scene

---

## 🎥 Demo

| Original Frame | AI Graded Frame |
|---|---|
| ![Before](assets/before.png) | ![After](assets/after.png) |

> Scene analysis table printed in terminal during pipeline run:

![Pipeline Terminal](assets/pipeline.png)

> Gradio web interface:

![Gradio UI](assets/gradio_ui.png)

---

## 🔁 Pipeline

```
Video input
    │
    ▼
Scene boundary detection      ←  PySceneDetect (finds every cut point)
    │
    ▼
Keyframe extraction            ←  OpenCV (1 frame per scene)
    │
    ▼
Cinematography analysis        ←  Gemini 2.5 Flash Vision (returns JSON)
    │
    ▼
Color grading per scene        ←  OpenCV float32 + .cube LUT
    │
    ▼
PDF report generation          ←  fpdf2 (keyframes + director notes)
    │
    ▼
Graded video export            ←  OpenCV VideoWriter
```

---

## 🛠️ Tech Stack

| Component | Tool |
|---|---|
| Vision + language analysis | Google Gemini 2.5 Flash (`google-genai`) |
| Scene detection | PySceneDetect |
| Image and video processing | OpenCV, NumPy |
| Color grading | OpenCV float32 pipeline + `.cube` LUTs |
| PDF report | fpdf2 |
| Web interface | Gradio |

---

## 📁 Project Structure

```
CineGrade-AI/
│
├── main.py                  # pipeline coordinator — run this
├── scene_detector.py        # finds scene cuts, extracts keyframes
├── frame_analyzer.py        # sends frames to Gemini, parses JSON response
├── color_grader.py          # applies brightness/contrast/saturation/LUT per scene
├── report_generator.py      # builds the PDF report
├── app.py                   # Gradio web interface
│
├── lut/                     # 13 professional .cube LUT files
│   ├── magic_hour.cube
│   ├── dark_somber.cube
│   ├── orange_and_blue.cube
│   └── ...
│
├── assets/                  # images used in this README
│   ├── banner.png
│   ├── before.png
│   ├── after.png
│   ├── pipeline.png
│   └── gradio_ui.png
│
└── requirements.txt
```

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/Mohit485/CineGrade-AI.git
cd CineGrade-AI
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get a free Gemini API key

Go to [aistudio.google.com](https://aistudio.google.com) → click **Get API key** → free, no credit card needed.

Then set it in your terminal:

```bash
# Mac / Linux
export GOOGLE_API_KEY="your_key_here"

# Windows
set GOOGLE_API_KEY=your_key_here
```

### 4. Add your LUT files

Place your `.cube` files inside the `lut/` folder. The pipeline expects these 13 files:

```
dark_somber.cube         hard_boost.cube          long_beach_morning.cube
lush_green.cube          magic_hour.cube          natural_boost.cube
orange_and_blue.cube     soft_bw.cube             waves.cube
blue_architecture.cube   blue_hour.cube           cold_chrome.cube
crisp_autumn.cube
```

---

## 🚀 Usage

### Option 1 — Terminal (no UI needed)

```bash
python main.py your_video.mp4
```

Output files are saved to `output/`:

```
output/
├── graded_video.mp4          ←  color graded result
├── analysis_report.pdf       ←  scene-by-scene PDF report
├── analysis_data.json        ←  raw Gemini analysis for every scene
└── keyframes/                ←  extracted keyframe images
```

### Option 2 — Gradio Web Interface

```bash
python app.py
```

Open `http://localhost:7860` in your browser. Upload a video, click **Analyze & Grade Video**, and see the original and graded video side by side with the full analysis.

---

## 🎨 How the Color Grading Works

Gemini Vision analyzes each keyframe and returns a structured JSON object like this:

```json
{
  "scene_description": "Golden hour exterior shot of a narrow street",
  "mood": "warm",
  "issues": ["slightly underexposed", "low saturation"],
  "director_note": "Boost warmth and exposure to bring out the golden feel of the light.",
  "adjustments": {
    "brightness": 20,
    "contrast": 15,
    "saturation": 1.3,
    "color_temp": "warm",
    "lut": "magic_hour"
  }
}
```

These values drive OpenCV math applied to every pixel in that scene:

| Adjustment | What it does |
|---|---|
| `brightness` | Adds a constant offset to every pixel value |
| `contrast` | Scales pixel values around midpoint 128 — darks darker, brights brighter |
| `saturation` | Converts to HSV, scales the S channel, converts back |
| `color_temp` | Scales R and B channels individually — warm = more red, less blue |
| `lut` | Applies a 3D `.cube` lookup table for the final cinematic film look |

> **Why float32?** The entire grading pipeline runs in float32 and converts back to uint8 only once at the final step. Converting between int and float repeatedly at each adjustment step causes tiny rounding errors that accumulate differently across frames, producing visible flickering. Float32 throughout eliminates this completely.

---

## 🎞️ LUT Library

| LUT | Best suited for |
|---|---|
| `magic_hour` | Golden hour, sunset, sunrise |
| `dark_somber` | Moody, noir, dark dramatic scenes |
| `hard_boost` | High contrast action and dramatic shots |
| `long_beach_morning` | Soft hazy morning light |
| `lush_green` | Nature, forests, greenery |
| `natural_boost` | General natural daylight |
| `orange_and_blue` | Cinematic blockbuster look |
| `soft_bw` | Emotional, minimalist, black and white feel |
| `waves` | Ocean, water, coastal scenes |
| `blue_architecture` | Urban, buildings, city environments |
| `blue_hour` | Dusk, twilight, blue tones |
| `cold_chrome` | Futuristic, sterile, cold environments |
| `crisp_autumn` | Fall colors, warm earth tones |

---

## ⚠️ Limitations

- Gemini 2.5 Flash free tier allows approximately **25 requests per day** — suitable for short clips up to ~25 scenes per day
- **Audio is not preserved** in the output video — can be remuxed manually using FFmpeg if needed:
  ```bash
  ffmpeg -i graded_video.mp4 -i original.mp4 -c copy -map 0:v -map 1:a final.mp4
  ```
- LUT files are **not included** in this repo due to licensing — source free `.cube` LUTs from [IWLTBAP](https://iwltbap.com) or similar

---

## 👤 Author

**Mohit**
Final year B.Tech — Artificial Intelligence & Machine Learning
JB Institute of Technology, Dehradun

[![GitHub](https://img.shields.io/badge/GitHub-Mohit485-black?style=flat-square&logo=github)](https://github.com/Mohit485)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat-square&logo=linkedin)](https://linkedin.com/in/YOUR_PROFILE)

---

## 📄 License

This project is licensed under the MIT License — feel free to use, modify, and distribute.