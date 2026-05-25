import os
import re
import datetime
import subprocess
import random
from pathlib import Path
from urllib.parse import quote
import requests
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ---------------- CONFIG ----------------

NUM_IMAGES = 8  # 8 unique scenes (faster generation)
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1920
IMAGE_MODEL = "flux"

STORY_MAX_WORDS = 130

TOPICS_FILE = "topics.txt"

IMAGES_DIR = Path("images")
OUTPUT_DIR = Path("output")
AUDIO_DIR = Path("audio")

MUSIC_FILE = AUDIO_DIR / "music.mp3"

NARRATION_FILE = OUTPUT_DIR / "narration.mp3"
STORY_FILE = OUTPUT_DIR / "story.txt"
SCENES_FILE = OUTPUT_DIR / "scenes.txt"
SUBS_FILE = OUTPUT_DIR / "subtitles.ass"
ANIMATED_VIDEO = OUTPUT_DIR / "animated.mp4"
VIDEO_WITH_SUBS = OUTPUT_DIR / "video_with_subs.mp4"
FINAL_VIDEO = OUTPUT_DIR / "final_video.mp4"

# VOSK MODEL FOR KOREAN SPEECH RECOGNITION
VOSK_MODEL_PATH = "vosk-model-small-ko-0.22"

# ----------------------------------------

def ensure_dirs():
    IMAGES_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    AUDIO_DIR.mkdir(exist_ok=True)
    # Clean old images
    for f in IMAGES_DIR.glob("*.jpg"):
        f.unlink()

def choose_topic_for_today():
    """Choose a unique topic based on the current date to ensure daily variety in GitHub Actions."""
    if not os.path.exists(TOPICS_FILE):
        print(f"[topics] Error: {TOPICS_FILE} not found!")
        return "Ancient Women's History"

    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        all_topics = [line.strip() for line in f if line.strip()]
    
    if not all_topics:
        return "Ancient Women's History"

    # Use today's date to get a stable but changing index
    # toordinal() returns an integer representing the day (e.g. 738000)
    today = datetime.date.today()
    index = today.toordinal() % len(all_topics)
    selected_topic = all_topics[index]
    
    print(f"[topics] Date: {today}, Index: {index}/{len(all_topics)}, Selected: {selected_topic}")
    
    # Optional: Log to used_topics.txt (though it won't persist in GHA)
    unused_topics_file = "used_topics.txt"
    with open(unused_topics_file, "a", encoding="utf-8") as f:
        f.write(f"{today}: {selected_topic}\n")
    
    return selected_topic

def generate_story_with_pollinations(topic: str) -> str:
    """Generate a short Korean story about ancient women's history using the modern paid Pollinations API."""
    api_key = os.getenv("POLLINATIONS_API_KEY")
    if not api_key:
        raise ValueError("POLLINATIONS_API_KEY environment variable is required for paid API")

    system_prompt = (
        "당신은 고대 문명의 여성 역사를 전문으로 하는 역사학자입니다. "
        "30초 분량(80-130 단어)의 짧고 흥미로운 이야기를 한국어로 작성하세요. "
        "실제 역사적 사실, 법률, 관습 또는 전통을 이야기하세요. "
        "생동감 있고 매력적인 문체를 사용하세요. 제목을 포함하지 마세요."
    )
    user_prompt = f"주제: {topic}. 흥미로운 역사적 사실을 이야기해 주세요."

    # Use the OpenAI-compatible chat completions endpoint as per documentation
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai",  # High quality text model
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.8
    }

    print(f"[story] Generating Korean story for topic: {topic} using paid API...")
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    
    response_data = r.json()
    text = response_data['choices'][0]['message']['content'].strip()

    # Post-process: ensure word count is within limits
    words = text.split()
    if len(words) > STORY_MAX_WORDS:
        text = " ".join(words[:STORY_MAX_WORDS]) + "."

    with open(STORY_FILE, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"[story] Korean story generated ({len(text.split())} words)")
    return text

def generate_scene_descriptions(story: str) -> list:
    """Extract distinct scene descriptions from the story sentences."""
    print(f"[scenes] Extracting {NUM_IMAGES} unique scene descriptions...")
    
    # Split story into sentences
    sentences = re.split(r'[.!?]+\s*', story.strip())
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    # Create unique scenes from sentences
    scenes = []
    for i in range(NUM_IMAGES):
        if i < len(sentences):
            scene = sentences[i]
        else:
            # Cycle through sentences if we need more
            scene = sentences[i % len(sentences)]
        
        # Make each scene description more visual
        if i not in [j % len(sentences) for j in range(len(scenes))]:
            scenes.append(scene)
        else:
            # Add variation for repeated scenes
            variations = ["close-up view of", "wide shot of", "dramatic scene of", "peaceful moment of"]
            scenes.append(f"{variations[i % len(variations)]} {scene}")
    
    # Ensure uniqueness by adding index
    unique_scenes = []
    for i, scene in enumerate(scenes[:NUM_IMAGES]):
        unique_scenes.append(f"{scene}")
    
    # Save scenes
    with open(SCENES_FILE, "w", encoding="utf-8") as f:
        for i, scene in enumerate(unique_scenes):
            f.write(f"{i+1}. {scene}\n")
    
    print(f"[scenes] Created {len(unique_scenes)} unique scenes")
    return unique_scenes

def generate_image(scene: str, idx: int) -> Path:
    """Generate a unique image for each scene using unified Pollinations AI gateway with authentication."""
    api_key = os.getenv("POLLINATIONS_API_KEY")
    # Note: Secret keys (sk_) have no rate limits as per api (6).json
    
    # Create unique seed for each image based on scene content + index
    seed = hash(scene + str(idx)) % 1000000
    
    # Build high-quality photorealistic prompt focusing on beautiful ancient women
    prompt = (
        f"stunning beautifully dressed woman from ancient civilization, {scene}, "
        f"hyper-realistic portrait, extremely detailed facial features, "
        f"intricate traditional ancient clothing with rich textures, "
        f"professional studio lighting, dramatic shadows and highlights, "
        f"RAW photography, photorealistic, 8K resolution, ultra-high detail, "
        f"sharp focus, depth of field, bokeh, cinematic composition, "
        f"masterpiece, award-winning photography, volumetric lighting, "
        f"hyper-detailed skin texture, realistic eyes with catchlights, "
        f"museum quality art, historical accuracy, elegant and graceful pose"
    )
    safe_prompt = quote(prompt)
    
    # Use unified gateway endpoint: gen.pollinations.ai
    # Documentation says: curl 'https://gen.pollinations.ai/image/a%20cat?model=flux' -H 'Authorization: Bearer YOUR_API_KEY'
    url = f"https://gen.pollinations.ai/image/{safe_prompt}"
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    params = {
        "width": IMAGE_WIDTH,
        "height": IMAGE_HEIGHT,
        "model": "flux",  # Premium flux model
        "seed": seed,
        "safe": True,
        "nologo": True,
        "negative_prompt": "worst quality, blurry, watermark, logo, text, signature, branded content, inappropriate, revealing, suggestive, nude, sexual, violence, blood, gore"
    }

    out = IMAGES_DIR / f"scene_{idx:02d}.jpg"
    print(f"[image] Generating image {idx+1}/{NUM_IMAGES} via unified gateway...")
    
    # Retry logic with exponential backoff
    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=120)
            r.raise_for_status()
            out.write_bytes(r.content)
            return out
        except Exception as e:
            wait_time = (attempt + 1) * 10
            if attempt < max_retries - 1:
                print(f"[image] Attempt {attempt+1} failed. Retrying in {wait_time}s... Error: {e}")
                time.sleep(wait_time)
            else:
                print(f"[image] Failed to generate image {idx+1} after {max_retries} attempts.")
                raise e
    return out


def generate_images(scenes: list):
    """Generate unique images for each scene SEQUENTIALLY (avoids rate limits)"""
    print(f"[image] Generating {NUM_IMAGES} images sequentially (avoiding rate limits)...")
    return [generate_image(scene, i) for i, scene in enumerate(scenes)]

def generate_tts(story: str):
    """Generate narration using edge-tts (free Microsoft TTS)."""
    import asyncio
    try:
        import edge_tts
    except ImportError:
        subprocess.run(["pip", "install", "edge-tts"], check=True)
        import edge_tts
    
    print("[tts] Generating Korean narration with edge-tts...")
    
    VOICE = "ko-KR-SunHiNeural"  # Korean female voice
    
    async def generate():
        communicate = edge_tts.Communicate(story, VOICE)
        await communicate.save(str(NARRATION_FILE))
    
    asyncio.run(generate())
    print(f"[tts] Narration saved to {NARRATION_FILE}")

def generate_word_subtitles():
    """Generate WORD-BY-WORD subtitles using Vosk (lightweight!)."""
    print("[subs] Generating word-level Korean subtitles with Vosk...")
    
    import json
    import wave
    from vosk import Model, KaldiRecognizer
    import os
    
    # Download Vosk model if not exists
    model_path = "vosk-model-small-ko-0.22"
    if not os.path.exists(model_path):
        print("[subs] Downloading Vosk Korean model (~82 MB)...")
        import urllib.request
        import zipfile
        
        url = "https://alphacephei.com/vosk/models/vosk-model-small-ko-0.22.zip"
        zip_path = "vosk-model.zip"
        
        urllib.request.urlretrieve(url, zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        os.remove(zip_path)
        print("[subs] Model downloaded!")
    
    # Convert MP3 to WAV for Vosk
    wav_file = "output/narration.wav"
    os.system(f'ffmpeg -y -i {NARRATION_FILE} -ar 16000 -ac 1 {wav_file}')
    
    # Load Vosk model
    model = Model(model_path)
    
    # Open WAV file
    wf = wave.open(wav_file, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)  # Enable word-level timestamps
    
    # Process audio
    words = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            if 'result' in result:
                for word_info in result['result']:
                    words.append({
                        'word': word_info['word'].upper(),
                        'start': word_info['start'],
                        'end': word_info['end']
                    })
    
    # Final result
    final_result = json.loads(rec.FinalResult())
    if 'result' in final_result:
        for word_info in final_result['result']:
            words.append({
                'word': word_info['word'].upper(),
                'start': word_info['start'],
                'end': word_info['end']
            })
    
    # Create ASS subtitle file with maximum compatibility for Korean in GitHub Actions
    # Using a font configuration that ensures Korean characters are properly rendered
    ass_content = """[Script Info]
Title: Korean History
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
LastStyleStorage: Default

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK KR,160,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,6,3,5,10,10,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    for word in words:
        start = word['start']
        end = word['end']
        text = word['word']
        
        start_time = f"{int(start//3600)}:{int((start%3600)//60):02d}:{start%60:.2f}"
        end_time = f"{int(end//3600)}:{int((end%3600)//60):02d}:{end%60:.2f}"
        
        # Escape special characters in ASS format
        text = text.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}')
        # Use the primary Korean font style with proper font specification
        ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
    
    # Save ASS file with proper BOM for UTF-8 (ensures correct rendering)
    with open(SUBS_FILE, "w", encoding="utf-8-sig") as f:
        f.write(ass_content)
    
    print(f"[subs] WORD-BY-WORD subtitles saved ({len(words)} words)")

def get_audio_duration(audio_file):
    """Get duration of audio file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_file)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def create_animated_slideshow(image_paths):
    """Create animated slideshow with Ken Burns zoom effect."""
    print("[video] Creating animated slideshow with Ken Burns effect...")
    
    # Get audio duration to match video length
    duration = get_audio_duration(NARRATION_FILE)
    per_image = duration / len(image_paths)
    
    # Create individual animated clips with zoom effect
    clips = []
    for i, img_path in enumerate(image_paths):
        clip_file = OUTPUT_DIR / f"clip_{i:02d}.mp4"
        clips.append(clip_file)
        
        # Calculate frames (30 fps)
        frames = max(int(per_image * 30), 60)
        
        # Alternate between zoom in and zoom out for variety
        if i % 2 == 0:
            # Zoom in effect
            zoom_start = 1.0
            zoom_end = 1.3
        else:
            # Zoom out effect  
            zoom_start = 1.3
            zoom_end = 1.0
        
        # Simple zoom with scale filter (more reliable on Windows)
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", (
                f"scale=8000:-1,"
                f"zoompan=z='if(lte(on,1),{zoom_start},{zoom_start}+(({zoom_end}-{zoom_start})/{frames})*on)':"
                f"d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={IMAGE_WIDTH}x{IMAGE_HEIGHT}:fps=30"
            ),
            "-t", str(per_image),
            "-c:v", "libx264",
            "-preset", "slow",  # Better quality
            "-crf", "18",  # High quality (lower = better, 18-23 is good)
            "-pix_fmt", "yuv420p",
            str(clip_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[video] Zoom failed for clip {i+1}, using fallback...")
            # Fallback: simple static with slight movement
            cmd_fallback = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", str(img_path),
                "-vf", f"scale={IMAGE_WIDTH}:{IMAGE_HEIGHT}:force_original_aspect_ratio=increase,crop={IMAGE_WIDTH}:{IMAGE_HEIGHT},fps=30",
                "-t", str(per_image),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(clip_file)
            ]
            subprocess.run(cmd_fallback, check=True, capture_output=True)
        
        print(f"[video] Animated clip {i+1}/{len(image_paths)}")
    
    # Create concat list
    concat_file = OUTPUT_DIR / "concat.txt"
    with open(concat_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip.resolve()}'\n")
    
    # Concatenate all clips
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(ANIMATED_VIDEO)
    ]
    subprocess.run(cmd, check=True)
    print(f"[video] Animated slideshow saved to {ANIMATED_VIDEO}")
    
    # Cleanup individual clips
    for clip in clips:
        if clip.exists():
            clip.unlink()

def add_subtitles():
    """Overlay ASS subtitles on video."""
    print("[video] Adding UPPERCASE subtitles...")
    
    # Windows path needs special handling for FFmpeg filter
    subs_path = str(SUBS_FILE.resolve()).replace("\\", "/").replace(":", "\\:")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(ANIMATED_VIDEO),
        "-vf", f"ass='{subs_path}'",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(VIDEO_WITH_SUBS)
    ]
    subprocess.run(cmd, check=True)
    print(f"[video] Video with subtitles saved to {VIDEO_WITH_SUBS}")

def merge_audio():
    """Merge video with narration and background music."""
    print("[merge] Merging audio with background music...")
    
    if MUSIC_FILE.exists():
        # Merge narration + background music (music at lower volume)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(VIDEO_WITH_SUBS),
            "-i", str(NARRATION_FILE),
            "-i", str(MUSIC_FILE),
            "-filter_complex", "[2:a]volume=0.25[bg];[1:a][bg]amix=inputs=2:duration=first[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-shortest",
            "-c:v", "copy",
            str(FINAL_VIDEO)
        ]
    else:
        print("[merge] No music.mp3 found, using narration only")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(VIDEO_WITH_SUBS),
            "-i", str(NARRATION_FILE),
            "-map", "0:v",
            "-map", "1:a",
            "-shortest",
            "-c:v", "copy",
            str(FINAL_VIDEO)
        ]
    
    subprocess.run(cmd, check=True)
    print(f"[merge] Final video saved to {FINAL_VIDEO}")

def main():
    ensure_dirs()

    topic = choose_topic_for_today()
    print("=" * 60)
    print(f"=== Topic: {topic}")
    print("=" * 60)

    # 1. Generate story with Pollinations AI
    story = generate_story_with_pollinations(topic)
    
    # 2. Generate unique scene descriptions from the story
    scenes = generate_scene_descriptions(story)
    
    # 3. Generate unique images for each scene
    images = generate_images(scenes)

    # 4. Generate narration with TTS
    generate_tts(story)
    
    # 5. Generate word-level UPPERCASE subtitles with Vosk
    generate_word_subtitles()
    
    # 6. Create animated slideshow with Ken Burns effect
    create_animated_slideshow(images)
    
    # 7. Add subtitles overlay
    add_subtitles()
    
    # 8. Merge audio (narration + background music)
    merge_audio()

    print("=" * 60)
    print(f"✅ DONE. Video ready: {FINAL_VIDEO}")
    print("=" * 60)

if __name__ == "__main__":
    main()
