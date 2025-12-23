import os
import sys
import google_clients
import config
import audit_research # Import the new research module
import video_generation # Import the video generation module
from dotenv import load_dotenv
import openai # Needed for the client object

# --- 0. Setup ---
print("--- [START] Marketing Audit Agent ---")
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("❌ FATAL ERROR: OPENAI_API_KEY not found in .env file.")
    sys.exit()

# Initialize OpenAI Client
try:
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI client initialized.")
except Exception as e:
    print(f"❌ FATAL ERROR: Could not initialize OpenAI client. {e}")
    sys.exit()


# --- 1. Connect to Google Services ---
print("\nConnecting to Google services...")
try:
    g_clients = google_clients.GoogleClients()
    if not g_clients.drive_service:
        raise Exception("Drive service failed to initialize.")
    print("✅ Google services connected.")
except Exception as e:
    print(f"❌ FATAL ERROR: Could not connect to Google. {e}")
    sys.exit()

# --- 2. Inputs ---
# These match your current client target
# *** UPDATED CLIENT TARGET: Bn Touch ***
INPUT_CLIENT_NAME = "BnTouch" 
# CORRECTED URL: Using the proper domain name.
INPUT_CLIENT_WEBSITE = "https://bntouch.com/" 
print(f"\nReceived Job for Client: '{INPUT_CLIENT_NAME}'")

# --- 3. Locate Main Project Folder ---
print(f"Connecting to main project folder...")
main_folder_id = config.MAIN_DRIVE_FOLDER_ID
if not main_folder_id:
    print("❌ FATAL ERROR: MAIN_DRIVE_FOLDER_ID not set in config.")
    sys.exit()

# --- 4. Locate or Create Client Folder ---
print(f"\nSearching for client folder in Drive...")
sanitized_client_name = "".join(c for c in INPUT_CLIENT_NAME if c.isalnum() or c in (' ', '-', '&')).rstrip()
client_folder_id = g_clients.find_or_create_folder(main_folder_id, sanitized_client_name)

if client_folder_id:
    print(f"✅ Found/Created Client Folder: '{sanitized_client_name}'")
else:
    print("❌ FATAL ERROR: Could not find or create client folder.")
    sys.exit()

# --- 5. Create Audit Specific Subfolders ---
audit_subfolders = [
    "01 Marketing Audit Report", 
    "02 Video Assets", 
    "03 Graphic Assets"
]

print(f"\nInitializing Audit Folders...")
audit_folder_ids = {}

for folder_name in audit_subfolders:
    f_id = g_clients.find_or_create_folder(client_folder_id, folder_name)
    if f_id:
        audit_folder_ids[folder_name] = f_id
    else:
        print(f"  ❌ Failed to create '{folder_name}'")

# --- 6. Execute Phase 6: Master Audit Generation ---
report_folder_id = audit_folder_ids.get("01 Marketing Audit Report")

# Initialize variables to hold outputs from the audit
website_summary = None
video_prompt_description = None
audit_link = None

if report_folder_id:
    print("\n--- Phase 6: Generating Master Audit Document ---")
    # This function call now correctly executes the audit and populates the necessary variables
    audit_link, website_summary, video_prompt_description = audit_research.run_master_audit(
        openai_client, INPUT_CLIENT_NAME, INPUT_CLIENT_WEBSITE, g_clients, report_folder_id
    )
    print(f"website_summary: {website_summary}")
    print( f"video_prompt_description: {video_prompt_description}")
    if audit_link:
        print(f"✅ Master Audit Document Generated and Uploaded: {audit_link}")
    else:
        print("❌ Master Audit Document Generation Failed.")
        
else:
    print("❌ Skipping Master Audit: Report folder not initialized.")
"""    
# Guard to ensure we have the data needed for the video phase
if not website_summary or not video_prompt_description:
    print("❌ Cannot proceed to video generation: Missing website summary or video prompt description from audit.")
    # We exit gracefully if the core audit data is missing
    sys.exit()


# --- 7. Execute Phase 7: Video Asset Generation ---
video_asset_folder_id = audit_folder_ids.get("02 Video Assets")

if video_asset_folder_id:
    print("\n--- Phase 7: Generating Video Asset ---")
    
    # 7.1 Generate Video Script (which acts as the main prompt for Sora)
    script_text = video_generation.generate_video_script(openai_client, website_summary, INPUT_CLIENT_NAME)
    
    if script_text:
        print("✅ Video Script/Prompt Generated.")
        
        # 7.2 Generate Video Asset using the prompt/script
        # We combine the descriptive prompt (from the audit) and the voiceover script for the AI
        full_video_prompt = f"{video_prompt_description}. Voiceover script: '{script_text}'."

        video_link = video_generation.generate_video_asset(
            full_video_prompt, INPUT_CLIENT_NAME, g_clients, video_asset_folder_id
        )
        
        if video_link:
            print(f"✅ Video Asset Generated and Uploaded: {video_link}")
        else:
            print("❌ Video asset generation failed.")
            
    else:
        print("❌ Video Script Generation Failed.")
        
else:
    print("❌ Skipping Video Generation: Video Assets folder not initialized.")
"""
print("\n--- [END] Marketing Audit Agent ---")