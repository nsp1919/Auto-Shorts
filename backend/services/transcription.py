from pathlib import Path
import openai
import os
from dotenv import load_dotenv

load_dotenv()

class Transcriber:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None
        
        # Lazy load local model only if needed (or if user wants free mode)
        self.local_model = None

    def _get_local_model(self):
        if not self.local_model:
            print("Loading local Whisper model (tiny)... This may take a moment.")
            from faster_whisper import WhisperModel
            # 'tiny' is fast and small. 'base' is better but larger.
            # Using 'int8' quantization for speed on CPU.
            # Upgraded to 'small' for better multi-language support (e.g. Telugu)
            self.local_model = WhisperModel("small", device="cpu", compute_type="int8")
        return self.local_model

    def transcribe_audio(self, audio_path: str, language: str = None) -> dict:
        """
        Transcribes audio using OpenAI Whisper API or Local Whisper (Fallback).
        Returns the full response object with segments (OpenAI format or similar dict).
        """
        if self.client:
            print("Using OpenAI Whisper API...")
            audio_file = open(audio_path, "rb")
            try:
                # Prepare arguments
                kwargs = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "response_format": "verbose_json",
                    "timestamp_granularities": ["segment", "word"]
                }
                # Force task to transcribe to prevent translation
                # Only add language if provided, otherwise auto-detect but keep task=transcribe
                if language:
                    kwargs["language"] = language
                elif language is not None:
                     # Explicitly allowed to be None for auto
                     pass
                
                # OpenAI API doesn't strictly need 'task' param for transcription as it is default, 
                # but explicit is better. However, creating translations is a different endpoint usually 
                # or different param. For chat completions it's different.
                # checking docs: yes, transcriptions.create is for transcription. translations.create is for translation.
                # So we are good on OpenAI side just by using the correct method. 
                # but let's be safe.
                
                transcript = self.client.audio.transcriptions.create(**kwargs)
                return transcript
            except Exception as e:
                print(f"OpenAI Transcription error: {e}")
                print("Falling back to local model...")
                # Allow fallback if API fails
            finally:
                audio_file.close()

        # Fallback / Free Mode
        try:
            print("Using Local Whisper (faster-whisper)...")
            model = self._get_local_model()
            
            # Prepare arguments
            # faster-whisper defaults to 'transcribe'. 
            # If we want to be safe, we can add task="transcribe"
            transcribe_kwargs = {"word_timestamps": True, "task": "transcribe"}
            if language:
                transcribe_kwargs["language"] = language
                
            segments, info = model.transcribe(audio_path, **transcribe_kwargs)
            
            print(f"   Detected language '{info.language}' with probability {info.language_probability}")

            # Convert generator to list and format like OpenAI response
            # OpenAI segment: {start, end, text, words: [{word, start, end}]}
            formatted_segments = []
            full_text = []

            for segment in segments:
                # print(f"   Segment: {segment.text}") # Debug print (Disabled to prevent Unicode errors on Windows console)
                seg_words = []
                if segment.words:
                    for w in segment.words:
                        seg_words.append({
                            "word": w.word,
                            "start": w.start,
                            "end": w.end
                        })
                
                formatted_segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": seg_words
                })
                full_text.append(segment.text)

            return {
                "text": " ".join(full_text),
                "segments": formatted_segments
            }

        except Exception as e:
            print(f"Local Transcription error: {e}")
            raise


transcriber = Transcriber()
