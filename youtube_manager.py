import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_client_config():
    raw = os.getenv("GOOGLE_CLIENT_JSON")
    if not raw:
        raise Exception("GOOGLE_CLIENT_JSON not set in ENV")
    return json.loads(raw)

def authorize_youtube():
    client_config = get_client_config()
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)  # Only works on PC
    # Save token for later
    with open("token.json", "w") as f:
        f.write(creds.to_json())
    return creds

def upload_video(video_file, title, description, tags=None):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        creds = authorize_youtube()
    
    youtube = build("youtube", "v3", credentials=creds)
    
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": "22"  # People & Blogs
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=video_file
    )
    response = request.execute()
    print("✅ Uploaded video:", response.get("id"))
    return response.get("id")
