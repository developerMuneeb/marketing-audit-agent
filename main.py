from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from video_generation import generate_video_asset, scrape_website_data, generate_video_prompt, get_drive_client, ensure_drive_folder, upload_to_drive
import anyio

app = FastAPI()

# Pydantic model to define expected input structure
class VideoRequest(BaseModel):
    name: str
    phone: str
    email: str
    company_name: str  # Only company_name and website will be used for video generation
    website: str  # Only company_name and website will be used for video generation
    consent: bool

@app.get("/")
def home():
    return {"message": "✅ FastAPI server is live. Use POST /generate-video with JSON body"}

@app.post("/generate-video/")
async def generate_video(request: VideoRequest):
    """
    API endpoint to generate a video based on client data (only company_name and website will be used for video generation).
    """
    # Extract the data from the request body
    name = request.name
    phone = request.phone
    email = request.email
    company_name = request.company_name  # Only this field will be passed to video generation
    website_url = request.website  # Only this field will be passed to video generation
    consent = request.consent

    print(f"📩 Received form data: {name}, {phone}, {email}, {company_name}, {website_url}, {consent}")

    # Scrape the website data using the provided website URL
    website_text = await anyio.to_thread.run_sync(scrape_website_data, website_url)  # Pass website_url to this function
    if not website_text:
        raise HTTPException(status_code=400, detail="Failed to scrape website data.")

    # Generate JSON prompt for video generation using the scraped website data and company name
    try:
        json_prompt = generate_video_prompt(company_name, website_text)  # No await, since the function is not async
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate video prompt: {str(e)}")

    # Generate the video based on the prompt
    local_video_path = generate_video_asset(json_prompt, company_name)

    if local_video_path:
        # Upload the video to Google Drive
        try:
            drive = get_drive_client()  # Get Google Drive client
            folder_id = ensure_drive_folder(drive, folder_name="Video Assets")  # Ensure the folder exists or create it
            upload_link = upload_to_drive(drive, folder_id, local_video_path, f"{company_name} - Video.mp4")  # Upload the video
            return {"message": "Video generated successfully", "video_path": local_video_path, "upload_link": upload_link}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload video to Drive: {str(e)}")
    else:
        raise HTTPException(status_code=500, detail="Video generation failed.")
    


# %%
