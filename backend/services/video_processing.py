import subprocess
import os
import shutil
from pathlib import Path


# Define available caption styles
# FFmpeg style format: key=value,key=value...
# Alignment=10 means centered (usually). 2 is bottom center.
STYLE_MAP = {
    "Karaoke": "Alignment=10,Fontname=Nirmala UI,Fontsize=30,PrimaryColour=&H00FF00&,OutlineColour=&H000000&,BorderStyle=1,Outline=1,Shadow=0,MarginV=20",
    "Deep Diver": "Alignment=10,Fontname=Nirmala UI,Fontsize=30,PrimaryColour=&HFFFFFF&,BorderStyle=3,Outline=1,Shadow=0,MarginV=20",  # Boxed
    "Mozi": "Alignment=10,Fontname=Nirmala UI,Fontsize=30,PrimaryColour=&HFF00FF&,OutlineColour=&HFFFF00&,BorderStyle=1,Outline=2,Shadow=0,MarginV=20",
    "Glitch": "Alignment=10,Fontname=Nirmala UI,Fontsize=30,PrimaryColour=&H0000FF&,OutlineColour=&H00FFFF&,BorderStyle=1,Outline=1,Shadow=1,MarginV=20",
    "Classic": "Alignment=10,Fontname=Nirmala UI,Fontsize=30,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,BorderStyle=1,Outline=1,Shadow=0,MarginV=20"
}

class VideoProcessor:
    def __init__(self, upload_dir: str = "uploads", output_dir: str = "processed"):
        self.upload_dir = Path(upload_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.ffmpeg_path = self._get_binary_path("ffmpeg")
        print(f"VideoProcessor initialized. FFmpeg path: {self.ffmpeg_path}")

    def add_watermark(self, video_path: str, output_path: str, 
                      watermark_text: str = None, 
                      watermark_image: str = None,
                      font_size: int = 24,
                      opacity: float = 0.8) -> str:
        """
        Adds a watermark to the video at bottom-right corner.
        watermark_text: Text to overlay (e.g., "@YourChannel")
        watermark_image: Path to PNG file for image watermark
        Returns path to watermarked video.
        """
        video_path = Path(video_path)
        output_path = Path(output_path)
        
        if watermark_text:
            # Text watermark using drawtext filter
            # Position: bottom-right with 20px padding
            # Semi-transparent black background box
            filter_str = (
                f"drawtext=text='{watermark_text}':"
                f"fontsize={font_size}:"
                f"fontcolor=white@{opacity}:"
                f"borderw=2:bordercolor=black@0.5:"
                f"x=w-tw-20:y=h-th-20"
            )
            
            command = [
                self.ffmpeg_path, "-y",
                "-i", str(video_path),
                "-vf", filter_str,
                "-c:a", "copy",
                str(output_path)
            ]
            
        elif watermark_image:
            # PNG watermark using overlay filter
            # Scale watermark to max 100px height, position bottom-right
            watermark_image = Path(watermark_image)
            if not watermark_image.exists():
                raise FileNotFoundError(f"Watermark image not found: {watermark_image}")
            
            filter_str = (
                f"[1:v]scale=-1:80[wm];"
                f"[0:v][wm]overlay=W-w-20:H-h-20"
            )
            
            command = [
                self.ffmpeg_path, "-y",
                "-i", str(video_path),
                "-i", str(watermark_image),
                "-filter_complex", filter_str,
                "-c:a", "copy",
                str(output_path)
            ]
        else:
            # No watermark, just copy
            shutil.copy(str(video_path), str(output_path))
            return str(output_path)
        
        try:
            print(f"Adding watermark: {' '.join(command)}")
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return str(output_path)
        except subprocess.CalledProcessError as e:
            print(f"Error adding watermark: {e}")
            raise

    def _get_binary_path(self, binary_name: str) -> str:
        """
        Attempts to find the binary path.
        1. Checks system PATH.
        2. Checks common WinGet location (recursive).
        """
        # 1. Check PATH
        path_in_env = shutil.which(binary_name)
        if path_in_env:
            return path_in_env
            
        # 2. Check WinGet Packages (Common User Install Location)
        # We need to find: AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_*/.../bin/binary_name.exe
        try:
            home = Path.home()
            winget_dir = home / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
            
            if winget_dir.exists():
                # Search for the binary recursively in this directory
                # Using rglob might be slow if many packages, but usually safe enough in Packages folder
                for path in winget_dir.rglob(f"{binary_name}.exe"):
                    if path.is_file():
                        return str(path)
        except Exception:
            pass

        # Fallback to just the name and hope
        return binary_name

    def extract_audio(self, video_path: str, output_audio_path: str = None) -> str:
        """
        Extracts audio from video using FFmpeg.
        Returns the path to the extracted audio file.
        """
        video_path = Path(video_path)
        if not output_audio_path:
            output_audio_path = self.output_dir / f"{video_path.stem}.mp3"
        
        command = [
            self.ffmpeg_path, "-i", str(video_path),
            "-q:a", "0", "-map", "a",
            str(output_audio_path), "-y"
        ]
        
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return str(output_audio_path)
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e}")
            raise

    def generate_word_level_srt(self, segments: list, output_path: str, start_offset: float = 0.0):
        """
        Generates an SRT file with fast-paced (word-level or small group) captions.
        segments: List of segment objects from Whisper verbose_json.
        start_offset: The start time of the video clip relative to the original video.
                        We subtract this from the transcript timestamps.
        """
        def format_timestamp(seconds: float):
            # SRT format: HH:MM:SS,ms
            if seconds < 0: seconds = 0
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds - int(seconds)) * 1000)
            return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

        entries = []
        counter = 1

        # Flatten all words if available, otherwise just use segments
        all_words = []
        for seg in segments:
            if "words" in seg:
                all_words.extend(seg["words"])
            else:
                # Fallback if no word level info: treat the whole segment as one (not ideal for shorts)
                all_words.append({
                    "word": seg["text"],
                    "start": seg["start"],
                    "end": seg["end"]
                })

        # Group words? For now, let's do 1-2 words per line for that "snappy" feel
        # or just 1 word if it's long? Let's do a simple greedy grouper: max 20 chars or 0.5 sec gap
        
        current_group = []
        
        for word_obj in all_words:
            w_start = word_obj["start"] - start_offset
            w_end = word_obj["end"] - start_offset
            text = word_obj["word"].strip()

            # Filter out things outside the clip
            # We assume we only got segments relevant to the clip, but double check keys
            if w_end < 0: continue
            
            # If start is negative but end is positive, clamp start
            if w_start < 0: w_start = 0

            # Simple logic: One word per line for maximum impact (users love this for shorts)
            # To make it slightly readable fast, maybe 1-2 words.
            # Let's stick to 1 word for "Karaoke" feel unless it's very short 'a', 'the', etc.
            
            entries.append((w_start, w_end, text))

        with open(output_path, "w", encoding="utf-8") as f:
            for start, end, text in entries:
                f.write(f"{counter}\n")
                f.write(f"{format_timestamp(start)} --> {format_timestamp(end)}\n")
                f.write(f"{text}\n\n")
                counter += 1
        
        return output_path

    def trim_source_video(self, video_path: str, output_path: str, start_time: float, end_time: float = None) -> str:
        """
        Trims the source video to a specific range. 
        Uses stream copy (-c copy) for speed if possible, but -ss before -i for fast seek.
        """
        video_path = Path(video_path)
        output_path = Path(output_path)
        
        command = [self.ffmpeg_path, "-y"]
        
        # Fast seek to start
        if start_time and start_time > 0:
            command.extend(["-ss", str(start_time)])
            
        command.extend(["-i", str(video_path)])
        
        # Duration or End Time
        if end_time:
            # If we used -ss before -i, timestamps are reset. 
            # So duration is simply (end - start).
            duration = end_time - start_time
            command.extend(["-t", str(duration)])
            
        # Use stream copy for speed since we are just trimming source
        # But stream copy on non-keyframe start might cause issues. 
        # For precise cutting, we should re-encode. 
        # Let's try re-encoding to be safe for analysis downstream, 
        # but maybe use a fast preset? 
        # Actually downstream (whisper, etc) handles audio.
        # Let's use re-encoding to ensure valid timestamps and keyframes for precise cuts later.
        command.extend(["-c:v", "libx264", "-preset", "fast", "-c:a", "aac"])
        
        command.append(str(output_path))
        
        print(f"Trimming source: {' '.join(command)}")
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return str(output_path)

    def cut_video(self, video_path: str, start_time: float, end_time: float, output_path: str = None, subtitle_path: str = None, style_name: str = "Classic", force_style_string: str = None) -> str:
        """
        Cuts a video segment using FFmpeg.
        start_time and end_time should be floats (seconds).
        If subtitle_path is provided, burns subtitles into the video using the specified style.
        force_style_string: Optional. If present, overrides style_name with this raw FFmpeg style string.
        """
        video_path = Path(video_path)
        if not output_path:
            output_path = self.output_dir / f"{video_path.stem}_cut.mp4"

        # -vf scale=-1:1920,crop=1080:1920 is for vertical 9:16 crop (center)
        vf_filters = ["scale=-1:1920,crop=1080:1920"]
        
        if subtitle_path:
            # FFmpeg requires escaping for Windows paths in filter arguments
            escaped_sub_path = str(Path(subtitle_path).absolute()).replace("\\", "/").replace(":", "\\:")
            
            # Get style string
            if force_style_string:
                style_str = force_style_string
            else:
                style_str = STYLE_MAP.get(style_name, STYLE_MAP["Classic"])
            
            # force_style applies these styles to ALL subtitles in the file
            vf_filters.append(f"subtitles='{escaped_sub_path}':force_style='{style_str}'")

        filter_complex = ",".join(vf_filters)

        # Note: -ss before -i is faster processing but timestamps reset. 
        # -ss after -i is frame-accurate. 
        # When burning subs, we need to be careful. The SRT we generated is relative to 0 (the start of the CLIP).
        # So we should seek to the start of the video, then read input?
        # Actually, if we use -ss before -i, the video starts at 0. So our 0-indexed SRT aligns perfectly.
        # But we need to use -t for duration, not -to.
        
        duration = end_time - start_time
        
        command = [
            self.ffmpeg_path, 
            "-ss", str(start_time),
            "-i", str(video_path),
            "-t", str(duration),
            "-vf", filter_complex,
            "-c:v", "libx264", "-c:a", "aac",
            str(output_path), "-y"
        ]

        try:
            print(f"Running FFmpeg: {' '.join(command)}")
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return str(output_path)
        except subprocess.CalledProcessError as e:
            print(f"Error cutting video: {e}")
            raise

video_processor = VideoProcessor()
