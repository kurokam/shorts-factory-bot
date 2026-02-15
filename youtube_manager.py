import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_youtube_service():
    token_json = os.getenv("YOUTUBE_TOKEN_JSON")
    if not token_json:
        raise Exception("YOUTUBE_TOKEN_JSON not set")

    creds = Credentials.from_authorized_user_info(
        json.loads(token_json), SCOPES
    )

    return build("youtube", "v3", credentials=creds)

def upload_video(video_path, title, description, tags=None):
    youtube = get_youtube_service()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(video_path)
    )

    response = request.execute()
    return response.get("id")
