import os
from instagrapi import Client
from pathlib import Path

class SocialMediaManager:
    def __init__(self):
        self.insta_client = None

    def login_instagram(self, username, password):
        try:
            cl = Client()
            cl.login(username, password)
            self.insta_client = cl
            return True
        except Exception as e:
            print(f"Instagram Login Failed: {e}")
            return False

    def upload_to_instagram(self, video_path: str, caption: str, username: str = None, password: str = None):
        """
        Uploads a video to Instagram Reels/Feed.
        """
        # Checks if we have credentials passed or in env
        # Note: Instagrapi login can trigger checkpoints. Use with caution.
        if not username:
            username = os.getenv("INSTAGRAM_USERNAME")
        if not password:
            password = os.getenv("INSTAGRAM_PASSWORD")
            
        if not username or not password:
             return {"success": False, "error": "No credentials provided"}

        try:
            cl = Client()
            # If we want to persist session, we should save settings.
            # keeping it simple: login every time (slow and risky for bans, but stateless)
            # A better way is to save session to a file.
            session_file = f"{username}_session.json"
            if os.path.exists(session_file):
                cl.load_settings(session_file)
                try:
                    cl.login(username, password)
                except:
                    # Session invalid, re-login
                    cl = Client()
                    cl.login(username, password)
            else:
                 cl.login(username, password)
                 cl.dump_settings(session_file)

            # Upload
            print(f"Uploading to Instagram: {video_path}")
            media = cl.video_upload(
                path=video_path,
                caption=caption
            )
            return {"success": True, "media_id": media.pk, "code": media.code}

        except Exception as e:
            print(f"Instagram Upload Error: {e}")
            return {"success": False, "error": str(e)}

social_manager = SocialMediaManager()
