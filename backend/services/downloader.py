import yt_dlp
from pathlib import Path
import uuid
from services.video_processing import video_processor

class VideoDownloader:
    def __init__(self, download_dir: str = "uploads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)

    def download_video(self, url: str) -> str:
        """
        Downloads a video from a URL (YouTube, generic) using yt-dlp.
        Returns the absolute path to the downloaded file.
        """
        file_id = str(uuid.uuid4())
        # Template: uploads/UUID.mp4
        output_template = str(self.download_dir / f"{file_id}.%(ext)s")

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'noplaylist': True,
        }

        if video_processor.ffmpeg_path and Path(video_processor.ffmpeg_path).is_absolute():
            ydl_opts['ffmpeg_location'] = video_processor.ffmpeg_path

        # Add robust options
        ydl_opts.update({
            'updatetime': False,
            'force_ipv4': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'quiet': True,
            'no_warnings': True,
        })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # yt-dlp might merge files and produce a filename different from the template extension if not forced
                # But typically 'best[ext=mp4]' tries to keep it mp4.
                # Let's find the actual file.
                
                # The info dict has 'filename' but sometimes it's the temp file.
                # The safest way with a predictable template is checking what exists.
                # But since we used uuid, we can search for it.
                
                # Prepare filename might fail if extension isn't in info dict yet
                # So we search for the file using the UUID we forced
                for file in self.download_dir.glob(f"{file_id}.*"):
                    return str(file.absolute())
                
                # Fallback if somehow glob fails but prepare_filename works (unlikely if glob failed)
                filename = ydl.prepare_filename(info)
                return str(Path(filename).absolute())
        except Exception as e:
            print(f"Download failed: {e}")
            raise

downloader = VideoDownloader()
