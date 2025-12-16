import subprocess
import json
import re
import os
import google.generativeai as genai
from pathlib import Path

class ContentAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None
            print("GEMINI_API_KEY not found. Analysis will fallback to heuristic.")


    def analyze_transcript(self, transcript_text: str, segments: list, duration: int = 60) -> list:
        """
        Analyzes the transcript to find the most viral/engaging segment.
        Returns a list of clips with start/end times.
        """
        if not self.model:
            print("No Gemini Model available for analysis. Using heuristics.")
            return []

        prompt = f"""
        Analyze the following video transcript segments and identify the most viral, funny, or engaging parts suitable for YouTube Shorts (under {duration} seconds each).
        
        Transcript Segments:
        {json.dumps(segments[:100])} ... (truncated)

        Return strictly valid JSON in this format:
        [
            {{
                "start": <start_time_in_seconds>,
                "end": <end_time_in_seconds>,
                "reason": "<short_reason_why_this_is_viral>",
                "score": <0.0_to_1.0>,
                "title": "<catchy_viral_title_for_youtube/instagram>",
                "description": "<engaging_description_for_social_media>",
                "hashtags": ["<hashtag1>", "<hashtag2>", ...]
            }}
        ]
        
        Focus on:
        1. High energy or emotional moments.
        2. Complete context (starts and ends clearly).
        3. Duration between 15s and {duration}s.
        4. Titles and descriptions should be clickbaity and viral-optimized.
        """

        try:
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            
            content = response.text
            viral_clips = json.loads(content)
            
            # Normalize if the LLM returns an object instead of list
            if isinstance(viral_clips, dict) and "clips" in viral_clips:
                viral_clips = viral_clips["clips"]
            elif isinstance(viral_clips, dict):
                 # Handle cases where it returns a single object wrapped in keys we didn't ask for
                 # Try to find a list or just wrap the dict
                 return [viral_clips] # blind hope
            
            return viral_clips

        except Exception as e:
            print(f"Analysis error: {e}")
            return []

    def generate_viral_content(self, video_context: str, clip_title: str = "", clip_reason: str = "") -> dict:
        """
        Generates viral captions, descriptions, and hashtags for social media sharing.
        Uses Gemini AI to analyze video context and create engaging content.
        
        Returns:
            dict: {
                "title": str,  # Catchy viral title
                "description": str,  # Engaging description with hook
                "hashtags": list,  # List of trending hashtags
                "caption_instagram": str,  # Instagram-optimized caption
                "caption_youtube": str  # YouTube-optimized description
            }
        """
        if not self.model:
            # Fallback content if no API
            return {
                "title": clip_title or "Check this out! 🔥",
                "description": "Amazing content you don't want to miss!",
                "hashtags": ["#viral", "#trending", "#fyp", "#foryou", "#explore"],
                "caption_instagram": f"{clip_title}\n\n#viral #trending #fyp #foryou #explore",
                "caption_youtube": clip_title or "Check this out!"
            }

        prompt = f"""
        Analyze this video clip context and generate viral social media content.
        
        Video Context/Transcript: {video_context[:2000]}
        Clip Title Hint: {clip_title}
        Why it's interesting: {clip_reason}
        
        Generate content optimized for MAXIMUM VIRALITY on Instagram and YouTube.
        Return strictly valid JSON:
        {{
            "title": "<catchy 5-10 word viral title with emoji>",
            "description": "<engaging 2-3 sentence description with hook and call-to-action>",
            "hashtags": ["<hashtag1>", "<hashtag2>", ... 15 trending hashtags without # symbol],
            "caption_instagram": "<full Instagram caption with emojis, line breaks, and hashtags at end>",
            "caption_youtube": "<YouTube description with timestamps placeholder and call-to-action>"
        }}
        
        Focus on:
        - Curiosity-inducing hooks ("You won't believe...", "This changed everything...")
        - Emotional triggers
        - Trending hashtags for 2024/2025
        - Platform-specific optimization
        """

        try:
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            content = response.text
            result = json.loads(content)
            
            # Ensure hashtags have # prefix
            if "hashtags" in result:
                result["hashtags"] = [f"#{tag.lstrip('#')}" for tag in result["hashtags"]]
            
            return result

        except Exception as e:
            print(f"Viral content generation error: {e}")
            return {
                "title": clip_title or "Must Watch! 🔥",
                "description": clip_reason or "You need to see this!",
                "hashtags": ["#viral", "#trending", "#fyp", "#foryou", "#explore", "#mustwatch"],
                "caption_instagram": f"{clip_title}\n\n#viral #trending #fyp",
                "caption_youtube": clip_title or "Check this out!"
            }

    def detect_high_energy_moments(self, video_path: str, num_clips: int = 4, clip_duration: int = 60) -> list:
        """
        Fallback: Selects interesting parts based on position (evenly distributed).
        """
        duration = self.get_video_duration(video_path)
        if not duration:
            return []

        clips = []
        
        # If total video is shorter than requested duration
        if duration <= clip_duration:
             return [{"start": 0, "end": duration, "score": 1.0, "reason": "Full video (short)"}]

        # Create 'num_clips' evenly spaced segments
        # Avoid the very end
        available_duration = duration - clip_duration
        if available_duration <= 0:
            available_duration = 0
            
        step = available_duration / (num_clips + 1) if num_clips > 0 else 0
        
        for i in range(num_clips):
            # i+1 to skip the very start (0.0) which might be an intro
            # Actually mixing it up: Start at 10%
            start_time = (step * (i + 1)) 
            
            # Ensure we don't go out of bounds
            if start_time + clip_duration > duration:
                start_time = max(0, duration - clip_duration)
            
            clips.append({
                "start": start_time,
                "end": start_time + clip_duration,
                "score": 0.8,
                "reason": f"Heuristic segment {i+1} (Fallback)"
            })
            
        return clips

    def get_video_duration(self, video_path: str) -> float:
        # Robustly find ffprobe using video_processor's discovered ffmpeg path as a hint
        from services.video_processing import video_processor
        
        ffmpeg_path = Path(video_processor.ffmpeg_path)
        # Assuming ffprobe is next to ffmpeg
        ffprobe_path = ffmpeg_path.parent / "ffprobe.exe"
        
        if ffprobe_path.exists():
             ffprobe_cmd = str(ffprobe_path)
        else:
             # Fallback to system path
             ffprobe_cmd = "ffprobe"

        command = [
            ffprobe_cmd, 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            str(video_path)
        ]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                print(f"ffprobe error: {result.stderr}")
                return 0.0
            return float(result.stdout.strip())
        except Exception as e:
            print(f"Error getting duration: {e}")
            return 0.0

analyzer = ContentAnalyzer()
