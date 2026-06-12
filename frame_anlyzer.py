# This file sends each keyframe image to Gemini and gets back
# cinematography analysis + specific grading instructions as JSON.
from google import genai
from google.genai import types
import os
import json
import base64
import time

def setup_gemini(): #Creates and returns a Gemini API client using your API key.
    api_key= os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("api_key not found"
                         "Run this in your terminal first:\n"
            "  export GOOGLE_API_KEY='your_key_here'\n")
    client= genai.Client(api_key= api_key)
    print("Gemini API Client created successfully")
    return client

def encode_image(image_path): #converts image into base64 text format so we can send it directly to APi call
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
def analyze_frames(client, image_path, scene_number): #Sends one keyframe image to Gemini and gets back analysis as a JSON dict
    print(f"Analyzing Scene {scene_number}...")
    image_data= encode_image(image_path)
    #prompt 
    prompt = """You are a professional cinematographer and colorist reviewing a film frame.
    Analyze this image and respond ONLY with a valid JSON object. No explanation, no markdown, no backticks. Just the raw JSON.
    
    The JSON must have exactly this structure:
    {
    "scene_description": "one sentence describing what is happening in the frame",
    "mood": "one word: dark / bright / warm / cold / dramatic / calm / tense / peaceful",
    "issues": ["list", "of", "problems", "you", "see"],
    "director_note": "one sentence of creative advice for this scene",
    "adjustments": {
        "brightness": 0,
        "contrast": 0,
        "saturation": 1.0,
        "color_temp": "neutral",
        "lut": "natural_boost"
    }
    }
    
    Rules for adjustment values:
    - brightness: integer -80 to +80. Negative = darken, positive = brighten.
    - contrast: integer -50 to +50. Negative = flatten, positive = more punch.
    - saturation: float 0.5 to 2.0. 1.0 = no change, 0.5 = grey, 1.8 = vivid.
    - color_temp: exactly one of: "warm" / "cool" / "neutral"
    -lut_style: pick the exact  most fitting ONE from this list based on the scene mood, or "none" if no LUT suits it:
    "dark_somber"        → dark, moody, dramatic scenes
    "hard_boost"         → high contrast punchy scenes, action or tension
    "long_beach_morning" → bright outdoor daylight, beach, morning scenes
    "lush_green"         → nature, forests, greenery, outdoor scenes
    "magic_hour"         → golden hour, sunset, romantic warm scenes
    "natural_boost"      → general natural look, slight enhancement, everyday scenes
    "orange_and_blue"    → strong teal-orange Hollywood blockbuster look
    "soft_bw"            → emotional, nostalgic, or timeless scenes, black and white
    "waves"              → water, ocean, coastal, fluid calm scenes
    "blue_architecture"  → urban, city, buildings, modern interiors
    "blue_hour"          → dusk, twilight, nighttime, dark blue atmosphere
    "cold_chrome"        → clinical, cold, sci-fi, desaturated metallic scenes
    "crisp_autumn"       → autumn foliage, warm earthy tones, fall season
    "none"               → if no LUT clearly fits this scene
 
Only suggest adjustments that genuinely improve cinematography. Use 0/1.0 for no change.
    """

    image_bytes= base64.b64decode(image_data)


    print(types.Part)
    print(types.Part.from_bytes)
    response= client.models.generate_content(
        model= "gemini-2.5-flash-lite",
        contents= [
            prompt,
            types.Part.from_bytes(data= image_bytes, mime_type= "image/jpeg")
            ]
    )

    raw_text= response.text.strip()
    if "{" in raw_text:
        start= raw_text.find("{")
        end= raw_text.rfind("}") +1 
        raw_text= raw_text[start:end]
    
    result= json.loads(raw_text) # Parse the JSON string into a Python dictionary
    result["scene_number"]= scene_number
    result["image_path"]= image_path
    return result

def analyze_all_frames(client, keyframe_paths, cache_path="output/analysis_cache.json"):
    import json
    # Load existing cache if it exists
    cache= {}
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            cached_list= json.load(f)
        # Convert list to dict keyed by image path for fast lookup
        cache= {item["item_path"]: item for item in cached_list}
    results = []

    for i, frame_path in enumerate(keyframe_paths):
        if frame_path in cache:
            result.append(cache[frame_path])
            print(f"  Scene {i+1}: loaded from cache (no API call)")
            continue

        try:
            result= analyze_frames(client, frame_path, scene_number= i+1)
            results.append(result)
            print(f"scene {i+1}: {result['mood']} | LUT: {result['adjustments']['lut']} | {result['scene_description'][:60]}...")

        except Exception as error:
            print(f"  Warning: Could not analyze scene {i+1}. Error: {error}")

        time.sleep(4)
    print(f"\nAnalyzed {len(results)} scenes successfully.")
    return results





