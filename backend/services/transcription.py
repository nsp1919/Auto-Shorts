from pathlib import Path
import openai
import os
from dotenv import load_dotenv

load_dotenv()

# Try to import faster-whisper, but make it optional for cloud deployment
# On Render, we skip this import entirely to save memory (loading libraries takes RAM)
FASTER_WHISPER_AVAILABLE = False
if not os.getenv("RENDER"):
    try:
        from faster_whisper import WhisperModel
        FASTER_WHISPER_AVAILABLE = True
    except ImportError:
        FASTER_WHISPER_AVAILABLE = False
        print("faster-whisper not available. Using OpenAI API only for transcription.")


class Transcriber:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None
        
        # Lazy load local model only if needed (or if user wants free mode)
        self.local_model = None

    def _get_local_model(self):
        # Prevent local model loading on Render to save memory
        if os.getenv("RENDER"):
             raise RuntimeError("Local Whisper model is disabled on Render to prevent memory crashes. Please set OPENAI_API_KEY.")

        if not FASTER_WHISPER_AVAILABLE:
            raise RuntimeError("faster-whisper is not installed. Please use OpenAI API or install faster-whisper locally.")
        if not self.local_model:
            print("Loading local Whisper model (tiny)... This may take a moment.")
            # 'tiny' is fast and small. 'base' is better but larger.
            # Using 'int8' quantization for speed on CPU.
            self.local_model = WhisperModel("tiny", device="cpu", compute_type="int8")
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
                "segments": formatted_segments,
                "detected_language": info.language
            }

        except Exception as e:
            print(f"Local Transcription error: {e}")
            raise

    def transcribe_with_roman_telugu(self, audio_path: str, language: str = None) -> dict:
        """
        Transcribes audio and converts Telugu text to Roman Telugu for captions.
        Use this for Instagram/YouTube style Telugu captions.
        """
        result = self.transcribe_audio(audio_path, language)
        
        # Check if Telugu was detected or specified
        detected_lang = result.get("detected_language", language)
        if detected_lang == "te" or language == "te":
            from services.transliteration import transliterate_telugu_to_roman, process_transcript_for_roman_telugu
            
            # Convert full text
            if "text" in result:
                result["text"] = transliterate_telugu_to_roman(result["text"])
            
            # Convert segments
            if "segments" in result:
                for segment in result["segments"]:
                    if "text" in segment:
                        segment["text"] = transliterate_telugu_to_roman(segment["text"])
                    if "words" in segment:
                        for word in segment["words"]:
                            if "word" in word:
                                word["word"] = transliterate_telugu_to_roman(word["word"])
            
            result["roman_telugu"] = True
        
        return result


transcriber = Transcriber()
