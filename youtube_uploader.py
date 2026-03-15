import os
import pickle
import time
import random
import http.client
import httplib2
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Explicitly tell the library that we are running locally for OAuth
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

class YouTubeUploader:
    def __init__(self, client_secrets_file='client_secrets.json'):
        self.client_secrets_file = client_secrets_file
        self.credentials = self._get_credentials()
        self.youtube = build(API_SERVICE_NAME, API_VERSION, credentials=self.credentials)

    def _get_credentials(self):
        creds = None
        # token.pickle stores the user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError(
                        f"❌ Missing '{self.client_secrets_file}'. "
                        "Please download it from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds

    def upload_video(self, file_path, title, description, category="10", privacy="private"):
        """
        Uploads a video to YouTube with resumable support
        """
        print(f"📡 Initializing YouTube upload: {title}")
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'category_id': category
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': False
            }
        }

        # Call the API's videos.insert method to create and upload the video.
        insert_request = self.youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
        )

        return self._resumable_upload(insert_request)

    def set_thumbnail(self, video_id, thumbnail_path):
        """
        Sets a thumbnail for a YouTube video
        """
        print(f"🖼️ Uploading thumbnail for video {video_id}...")
        try:
            request = self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            )
            response = request.execute()
            print("✅ Thumbnail uploaded successfully!")
            return response
        except HttpError as e:
            status_code = e.resp.status
            
            if status_code == 403:
                print("❌ Thumbnail upload denied (403 Forbidden)")
                print("\n💡 Possible causes:")
                print("   1. Missing YouTube scope in authentication")
                print("   2. Video is still processing (wait a few seconds)")
                print("   3. Thumbnail file format not supported")
                print("   4. File size exceeds 2MB limit")
                print("\n🔧 Solutions:")
                print("   • Delete token.pickle and re-authenticate")
                print("   • Ensure client_secrets.json has youtube.upload scope")
                print("   • Convert image to JPG and reduce size if needed")
                
            elif status_code == 400:
                print("❌ Invalid thumbnail (400 Bad Request)")
                print("💡 Requirements:")
                print("   • Format: JPG or PNG only")
                print("   • Max size: 2MB")
                print("   • Recommended: 1280x720 pixels")
                
            elif status_code == 404:
                print(f"❌ Video not found (404): {video_id}")
                print("💡 Make sure the video ID is correct")
                
            else:
                print(f"❌ Thumbnail upload failed ({status_code}): {e}")
            
            return None

    def _resumable_upload(self, request):
        response = None
        error = None
        retry = 0
        max_retries = 10
        
        print("🚀 Starting upload to YouTube...")
        
        while response is None:
            try:
                status, response = request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        print(f"✅ Video successfully uploaded! ID: {response['id']}")
                        print(f"🔗 Link: https://www.youtube.com/watch?v={response['id']}")
                        return response
                    else:
                        raise Exception(f"❌ The upload failed with an unexpected response: {response}")
                
                if status:
                    print(f"   📊 Upload progress: {int(status.progress() * 100)}%")
            
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    error = f"Retriable HTTP error {e.resp.status} occurred"
                else:
                    raise
            except (httplib2.HttpLib2Error, IOError) as e:
                error = f"Retriable error occurred: {e}"

            if error:
                print(f"⚠️  {error}. Retrying {retry+1}/{max_retries}...")
                retry += 1
                if retry > max_retries:
                    raise Exception("❌ No more retries left. Upload failed.")
                
                # Exponential backoff
                sleep_time = random.random() * (2**retry)
                time.sleep(sleep_time)
                error = None
        
        return None

if __name__ == "__main__":
    # Test stub
    print("YouTube Uploader Module Ready.")
