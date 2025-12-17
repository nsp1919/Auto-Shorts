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

        # Add robust options - REMOVED ignoreerrors to fail fast and see real error
        ydl_opts.update({
            'updatetime': False,
            'force_ipv4': True,
            'source_address': '0.0.0.0', # Bind to IPv4 interface
            'nocheckcertificate': True,
            'socket_timeout': 15,
            'retries': 10,
            # 'ignoreerrors': True, # Removed to debug
            # 'quiet': True,        # Removed to debug
            'no_warnings': True,
        })
        
        print(f"DEBUG: ydl_opts: {ydl_opts}")

        # DEBUG: Print version to ensure update worked
        import yt_dlp.version
        print(f"DEBUG: yt-dlp version: {yt_dlp.version.__version__}")

        # DEBUG: Test DNS resolution before yt-dlp
        import socket
        try:
            print(f"DEBUG: DNS Test google.com: {socket.gethostbyname('google.com')}")
            print(f"DEBUG: DNS Test youtube.com: {socket.gethostbyname('youtube.com')}")
        except Exception as e:
            print(f"DEBUG: DNS Test failed: {e}")

        # Strategy Order:
        # 1. Standard (Let system/yt-dlp decide, usually best for Docker)
        # 2. Force IPv4 (Fixes some IPv6-only network issues)
        # 3. User Agent Spoofing (Fixes some bot blocking)
        
        base_opts = ydl_opts.copy()
        if 'source_address' in base_opts:
            del base_opts['source_address']
        if 'force_ipv4' in base_opts:
            del base_opts['force_ipv4']

        attempts = [
            {"name": "Standard", "opts": {**base_opts}},
            # Fix: Use DNS over HTTPS (DoH) - Best for restricting environments
            {"name": "Google DoH", "opts": {**base_opts, 'doh_url': 'https://dns.google/dns-query', 'force_ipv4': True}}, 
            # Fallback to Cloudflare DoH
            {"name": "Cloudflare DoH", "opts": {**base_opts, 'doh_url': 'https://cloudflare-dns.com/dns-query', 'force_ipv4': True}},
            
            # Explicit DNS servers (UDP 53)
            {"name": "Google DNS", "opts": {**base_opts, 'dns_servers': ['8.8.8.8', '8.8.4.4'], 'force_ipv4': True}}, 
        ]
        
        # NOTE: 'dns_servers' is supported by yt-dlp to override socket.getaddrinfo behavior internally
        # provided the phython dependency versions support it.

        
        last_error = None

        for attempt in attempts:
            print(f"DEBUG: Trying download strategy: {attempt['name']}")
            try:
                with yt_dlp.YoutubeDL(attempt['opts']) as ydl:
                    info = ydl.extract_info(url, download=True)
                    
                    if info is None:
                        raise Exception("yt-dlp extract_info returned None")
                    
                    # Success!
                    # Find extracted file
                    # We look for files matching the ID because extensions vary (mp4, mkv, webm)
                    for file in self.download_dir.glob(f"{file_id}.*"):
                        return str(file.absolute())
                    
                    # Fallback if file not found by glob (shouldnt happen with outtmpl)
                    filename = ydl.prepare_filename(info)
                    return str(Path(filename).absolute())
                    
            except Exception as e:
                print(f"Strategy {attempt['name']} failed: {e}")
                last_error = e
                # Continue to next attempt
        
        # If all failed
        print(f"All download strategies failed. Last error: {last_error}")
        raise last_error

downloader = VideoDownloader()
