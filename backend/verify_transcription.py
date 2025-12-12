from services.transcription import transcriber
import os

# Find an mp3 file to test
processed_dir = "processed"
mp3_files = [f for f in os.listdir(processed_dir) if f.endswith(".mp3")]

if not mp3_files:
    print("No MP3 files found in processed/")
    exit(1)

test_file = os.path.join(processed_dir, mp3_files[0])
print(f"Testing transcription on: {test_file}")

try:
    result = transcriber.transcribe_audio(test_file)
    print("KEYS:", result.keys())
    print("TEXT LENGTH:", len(result.get("text", "")))
    print("SEGMENTS COUNT:", len(result.get("segments", [])))
    if result.get("segments"):
        print("FIRST SEGMENT:", result["segments"][0])
except Exception as e:
    print(f"ERROR: {e}")
