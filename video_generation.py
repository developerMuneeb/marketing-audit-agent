import os
import requests
import json
import re
import time
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from playwright.sync_api import sync_playwright
load_dotenv()
 
# ---------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------
SORA2_API_URL = os.environ.get("SORA2_API_URL")
SORA2_API_KEY = os.environ.get("SORA2_API_KEY")
SORA2_API_SECRET = os.environ.get("SORA2_API_SECRET")
client = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],  # this is also the default, it can be omitted
)
 
 
 
POLL_INTERVAL_SECONDS = 10
MAX_POLL_ATTEMPTS = 50  # increased to ensure video has time to complete
 
 
# Function to Ensure Google Drive Folder Exists
def ensure_drive_folder(drive, folder_name="Video Assets") -> str:
    """
    Checks if a folder exists in Google Drive. If it doesn't exist, it creates a new folder.
    Returns the folder ID as a string.
    """
    # Check if the folder exists in Google Drive
    file_list = drive.ListFile({'q': f"mimeType='application/vnd.google-apps.folder' and trashed=false and title='{folder_name}'"}).GetList()
   
    # If the folder exists, return its ID
    for f in file_list:
        if f['title'] == folder_name:
            return f['id']
   
    # If the folder doesn't exist, create it
    folder_metadata = {'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder['id']
 
def upload_to_drive(drive, folder_id, file_path, file_name):
    try:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            print("❌ Local file is empty — cannot upload.")
            return None

        print(f"📁 Local video OK — size: {file_size} bytes")

        # Create the Google Drive file
        file = drive.CreateFile({
            'title': file_name,
            'parents': [{'id': folder_id}],
            'mimeType': 'video/mp4'   # ⭐ FIX #1 (REQUIRED)
        })

        # Attach actual content
        file.SetContentFile(file_path)  # ⭐ FIX #2 (REQUIRED BEFORE Upload)

        file.Upload()  # Upload the file with its contents

        print(f"✅ Uploaded successfully: {file['title']} ({file.get('fileSize')} bytes)")
        return file.get('webContentLink')

    except Exception as e:
        print(f"❌ Error uploading file to Drive: {e}")
        return None

 
 
 
 
# ---------------------------------------------------
# GOOGLE DRIVE FUNCTIONALITY
# ---------------------------------------------------
def get_drive_client():
    gauth = GoogleAuth()
   
    # Check if token.json file exists (this contains saved credentials)
    if os.path.exists("token.json"):
        # Load saved credentials from the token.json file
        gauth.LoadCredentialsFile("token.json")
       
    # If credentials are not available or expired
    if not gauth.credentials or gauth.access_token_expired:
        # Perform the full authentication process
        gauth.LocalWebserverAuth()
   
    # Save the credentials for future use
    gauth.SaveCredentialsFile("token.json")
   
    drive = GoogleDrive(gauth)
    return drive
 
 
 
#Scrap Website Data
 
# Function to scrape website data
 
 


def scrape_website_data(url):
    print(f"🌐 Scraping website with browser: {url}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )

            page = context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
            except:
                page.goto(url, wait_until="load", timeout=60000)

            # Let Incapsula JS finish
            page.wait_for_timeout(4000)

            text = page.inner_text("body")

            browser.close()

            if not text.strip():
                print("❌ No content extracted")
                return None

            print("✅ Website scraped successfully via browser")
            return text[:6000]

    except Exception as e:
        print(f"❌ Browser scraping failed: {e}")
        return None

#------------------------------ Enforced Voice Over Rules ------------------------------

def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text.strip()))

def enforce_voiceover_rules(json_output: str) -> str:
    data = json.loads(json_output)

    vo = data.get("voice_over", {})
    script = vo.get("script", "")
    wc = count_words(script)

    # 1) Enforce word count (22–24)
    if wc > 24:
        words = script.split()
        script = " ".join(words[:24]) + "."
        vo["script"] = script
        wc = 24

    elif wc < 22:
        raise ValueError(f"Voiceover too short ({wc} words). Manual retry required.")
        

    # 2) Force correct VO timing + strict lip sync
    vo["duration_seconds"] = 9
    vo["delivery"] = "pre-recorded voiceover with strict lip sync"
    vo["lip_sync"] = True
    vo["lip_sync_mode"] = "strict"
    vo["pace"] = "brisk, clear, minimal pauses, finish by 9.5s"
    vo["end_behavior"] = (
        "end by 9.5s; lips close on final word and remain closed with a confident smile."
        
    )
    data["voice_over"] = vo

    # 3) Remove illegal top-level VO keys if the model outputs them
    for k in ["delivery", "lip_sync_mode", "pace", "end_behavior", "duration_seconds"]:
        if k in data:
            del data[k]

    # 4) Force subject behavior (no lip flaps after VO)
    subject = data["video"].get("subject", {})
    subject["lip_sync"] = True
    subject["expression"] = "confident, professional, friendly, subtly happy"
    subject["action"] = (
        (subject.get("action", "") + " ").strip() +
        "Speaks only during the voiceover; after speech ends, mouth stays closed with a confident, friendly smile until the final frame."
    )
    data["video"]["subject"] = subject

    # 5) Anti-lip-flap constraints
    constraints = data.get("constraints", {})
    constraints.update({
        "no_additional_dialogue": True,
        "mouth_lock_after_voiceover": True,
        "post_speech_pose": "closed-mouth confident smile",
        "continuous_scene_until_last_frame": True,
        "no_end_card": True,
        "no_color_flash": True
    })
    data["constraints"] = constraints

    return json.dumps(data, ensure_ascii=False, indent=2)


def generate_video_prompt(company_name, website_text, video_duration=12):
    """
    ONE SINGLE LLM CALL:
    - Analyzes full website content
    - Creates 10s voiceover script
    - Creates full Higgsfield JSON prompt
    - Returns final JSON string
    """
 
    system_prompt = """
You are an elite video-prompt engineer specializing in ultra-realistic JSON prompts for Higgsfield Sora-2.

OUTPUT RULE:
- Return ONLY a single valid JSON object.
- NO markdown, NO explanations, NO extra keys.

GOAL:
Using the company name and website content, generate a complete JSON prompt for a 12-second ultra-realistic UGC selfie-vlog video that aligns perfectly with the brand’s industry, tone, and audience.

BRAND & THEME ANALYSIS (internal reasoning):
Infer from the website:
- company services and niche
- target audience (B2B / B2C / enterprise / consumers)
- brand tone (professional, innovative, premium, friendly, etc.)
- the most natural OUTDOOR environment that visually supports the brand

VIDEO RULES (MANDATORY):
- Outdoor setting ONLY. Never indoors. Never studio.
- Front-facing smartphone selfie camera.
- Continuous forward walking for the ENTIRE clip.
- Natural handheld motion: arm sway, walking bob, micro-shakes.
- Visible background movement + parallax (people, traffic, environment).
- Scene must continue smoothly until the final frame with NO scene cuts, NO color flashes, NO end cards.

SUBJECT & EXPRESSION (CRITICAL):
- Subject must match brand archetype (e.g., professional in blazer for enterprise brands).
- Facial expression must be confident, calm, professional, and subtly positive (light smile or assured expression).
- Subject must NOT appear blank, robotic, or emotionless.
- Subject speaks ONLY during the voiceover.
- After the final word, the mouth closes naturally and remains closed.
- After speaking, the subject continues walking with a composed, confident expression until the final frame.

VOICEOVER ENFORCEMENT (MANDATORY):
- Script MUST be EXACTLY 22, 23, or 24 words (count carefully).
- If the script exceeds 24 words, rewrite it shorter.
- Voiceover must naturally finish between 9.5 and 10.5 seconds.
- All voiceover control keys MUST be inside the "voice_over" object only.
- The subject must NOT speak or move lips outside the voiceover duration.
- After the final word, mouth closes and remains closed with a confident, friendly expression.


CONSTRAINTS (STRICT):
- no_on_screen_text = true
- no_graphical_overlays = true
- no_indoor_or_studio_setting = true
- maintain_photorealism = true
- no_scene_transition = true
- no_end_card = true
- no_color_flash = true
- continuous_scene_until_last_frame = true

JSON STRUCTURE (exact keys only):
{
  "version": "1.4",
  "video": {
    "duration_seconds": 12,
    "style": "...",
    "camera": { ... },
    "subject": { ... },
    "environment": { ... }
  },
  {
  "delivery": "pre-recorded voiceover with strict lip sync",
  "duration_seconds": 10,
  "lip_sync_mode": "strict",
  "pace": "slower, controlled, finish near 10.0s",
  "end_behavior": "finish cleanly; lips close fully on the final word and remain closed"
  },

  "voice_over": {
    "enabled": true,
    "duration_seconds": 10,
    "script": "...(23–24 words)...",
    "tone": "professional",
    "language": "en-US",
    "lip_sync": true
  },
  "audio_sync": true,
  "constraints": { ... },
  "context": {
    "brand": "...",
    "company_summary": "...",
    "objective": "..."
  }
}

VALIDATION BEFORE OUTPUT:
1) JSON must parse correctly.
2) Outdoor environment confirmed.
3) Subject walking continuously until final frame.
4) Voiceover word count is EXACTLY 23–24 words.
5) Voiceover duration < video duration.
6) Mouth remains closed after speech.
7) No scene ending artifacts or color screens.

"""

    user_prompt = f"""
Company Name: {company_name}
 
Website Content:
{website_text}
 
TASK:
Analyze the website + brand deeply and produce the FULL JSON described above.
Remember: ONE output = the FINAL JSON ONLY.
"""
 
    try:
        completion = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
 
        json_output = completion.choices[0].message.content.strip()
        print("\n📦 RAW JSON FROM CHATGPT:")
        print(json_output)
        
        
        # ✅ enforce rules before sending to Higgsfield
        json_output = enforce_voiceover_rules(json_output)
        print("\n📦 FINAL JSON AFTER ENFORCEMENT:")
        
        
        
        return json_output


    except Exception as e:
        print(f"❌ Error generating unified prompt: {e}")
        return None
 
 
 
 
# ---------------------------------------------------
# GENERATE VIDEO AND DOWNLOAD
# ---------------------------------------------------
def generate_video_asset(json_prompt, client_name):
    if not SORA2_API_URL or not SORA2_API_KEY or not SORA2_API_SECRET:
        print("❌ SORA2 API keys missing.")
        return None
 
    headers = {
        "Content-Type": "application/json",
        "hf-api-key": SORA2_API_KEY,
        "hf-secret": SORA2_API_SECRET
    }
 
    payload = {
        "prompt": json_prompt,
        "duration": 12,
        "resolution": "720p",
        "aspect_ratio": "9:16"
    }
 
    print("🎬 Sending JSON prompt to SORA...")
    try:
        response = requests.post(SORA2_API_URL, headers=headers, json=payload)
        response_json = response.json()
    except Exception as e:
        print(f"❌ API POST failed: {e}")
        return None
 
    request_id = response_json.get("request_id")
    if not request_id:
        print(f"❌ SORA rejected request: {response_json}")
        return None
 
    print(f"⏳ Job queued: {request_id}")
 
    # Polling loop
    for attempt in range(MAX_POLL_ATTEMPTS):
        time.sleep(POLL_INTERVAL_SECONDS)
        print(f"[POLL {attempt+1}] Checking status...")
 
        status_url = f"https://platform.higgsfield.ai/requests/{request_id}/status"
        try:
            status_response = requests.get(status_url, headers=headers)
            status_data = status_response.json()
        except Exception as e:
            print(f"⚠️ Polling request failed: {e}")
            continue
 
        job_status = status_data.get("status")
        if job_status in ["completed", "succeeded"]:
            # Check multiple possible locations for video URL
            video_url = status_data.get("video_url") or (status_data.get("video") or {}).get("url")
            if video_url:
                print(f"⬇️ Downloading video from: {video_url[:50]}...")
                if not os.path.exists("temp_outputs"):
                    os.makedirs("temp_outputs")
                local_path = os.path.join("temp_outputs", f"{client_name} - Video.mp4")
                try:
                    video_content = requests.get(video_url).content
                    with open(local_path, "wb") as f:
                        f.write(video_content)
                    print(f"✅ Video saved locally: {local_path}")
                    return local_path
                except Exception as e:
                    print(f"❌ Failed to download video: {e}")
                    return None
            else:
                print("❌ Video URL not found in response.")
                return None
        elif job_status == "failed":
            print(f"❌ Video generation failed: {status_data.get('error')}")
            return None
 
    print(f"❌ Video generation timed out after {MAX_POLL_ATTEMPTS*POLL_INTERVAL_SECONDS} seconds.")
    return None
 
 
# ---------------------------------------------------
# MAIN
# ---------------------------------------------------
if __name__ == "__main__":
    client_name = input("Enter client name: ").strip()
    website_url = input("Enter client website URL: ").strip()
 
    # ALL of the following lines must be indented to be inside the 'if' block
   
    # Scrape website data to get the text
    website_text = scrape_website_data(website_url)
    print(website_text)
    # Generate JSON prompt (ensure this is generated properly before passing it to generate_video_asset)
    json_prompt = generate_video_prompt(client_name, website_text)
    print(json_prompt)
 
 
    # Generate video locally using the generated json_prompt
    local_video_path = generate_video_asset(json_prompt, client_name)
 
    if local_video_path:
        # Upload the video to Google Drive
        drive = get_drive_client()
        folder_id = ensure_drive_folder(drive, folder_name="Video Assets")  # Ensure folder exists or create
        upload_link = upload_to_drive(drive, folder_id, local_video_path, f"{client_name} - Video.mp4")
        print(f"✅ Video uploaded to Drive: {upload_link}")
    else:
        print("❌ Video generation failed. No local video created.")
 

