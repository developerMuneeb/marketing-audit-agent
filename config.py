# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# --- Google Sheet (Input Checklist) Configuration ---
# The ID of the Google Sheet containing your checklist.
SHEET_ID = '1IzUi018eEB61-NDwmvdjWcJdDnrUzsXf20JC_MhdXME' # <-- Make sure this is set

# --- Google Drive (Output Folder) Configuration ---
# The ID of the main Google Drive folder for SOPs.
MAIN_DRIVE_FOLDER_ID = '1s8jqFtl5cfLN8gP3XNK4aw_NUtEoYOdq' # <-- Make sure this is set
MAIN_DRIVE_FOLDER_NAME = 'Marketing Strategy Docs' # Used for display

# --- Log Sheet Configuration (Automated Creation) ---
# Names for the auto-created folder and sheet within the main Drive folder.
LOG_FOLDER_NAME = 'Logs'
LOG_SHEET_NAME = 'AI SOP Generation Log'

# --- AI Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Script Behavior Configuration ---
# Tabs in the input sheet to ignore.
IGNORE_TABS = ['Dashboard', '⚒️ Tools & Templates']

# --- Log Headers (for automated log sheet creation/new tabs) ---
# Column headers for the log sheet tabs.
LOG_HEADERS = ['Tab Name', 'Document Title', 'Drive Link', 'Status', 'Timestamp']