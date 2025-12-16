# Auto Post / Auto-Shorts Project Documentation

## 1. Project Overview
**Auto Post** (also referred to as **Auto-Shorts**) is an AI-powered web application designed to automatically repurpose long-form videos (such as podcasts, vlogs, and interviews) into viral short-form content (Shorts, Reels, TikToks).

It leverages AI to detect engaging moments, transcribe audio, and intelligently crop video to vertical (9:16) format while keeping the speaker in focus.

---

## 2. Features

### Core Features
- **Multi-Source Input**:
  - **File Upload**: Supports drag-and-drop for MP4, MOV, MKV files (up to 2GB).
  - **YouTube Integration**: Paste a YouTube URL (Video or Short) to download and process directly.
- **AI Moment Detection**: Automatically identifies high-energy, funny, or engaging segments using AI (GPT/Heuristics).
- **Smart Cropping (9:16)**: Uses dynamic face tracking to ensure the speaker remains centered in the vertical frame.
- **Viral Captions**: Adds animated, "Alex Hormozi-style" captions with emoji support.
- **Social Sharing**:
  - Direct upload to **Instagram** and **YouTube**.
  - **Rocket Share**: AI generation of titles, descriptions, and hashtags for posts.

### Customization Options
- **Caption Styles**:
  - **Karaoke**: Highlighted current word (Green/White).
  - **Deep Diver**: Boxed background style.
  - **Mozi**: Purple/Yellow border style.
  - **Glitch**: Red shadow/glitch effect.
  - **Classic**: Standard white text.
- **Visual Customization**:
  - Custom Text Color (#Hex).
  - Custom Background Color (for text boxes).
  - Font Size adjustments.
- **Clip Configuration**:
  - **Duration**: Presets for 30s, 60s, 90s, 120s.
  - **Quantity**: Generate 1 to 10 shorts at a time.
  - **Trimming**: Specify exact Start and End times for processing.
  - **Language**: English or Auto-Detect.

---

## 3. How It Works (Workflow)

The application follows a linear pipeline to transform content:

1.  **Input**: User uploads a file or pastes a YouTube URL.
2.  **Pre-Processing**:
    - If URL: Video is downloaded via `yt-dlp`.
    - If File: Uploaded to `backend/uploads/`.
    - (Optional) Video is trimmed to user-specified start/end times.
3.  **Audio Extraction**: Audio track is separated from the video.
4.  **Transcription**: `Whisper` (OpenAI or Local) transcribes the audio to text with timestamps.
5.  **Analysis**:
    - **LLM/AI**: Analyzes the transcript to find the most engaging "viral" moments.
    - **Heuristic Fallback**: Uses energy/volume levels if AI analysis is skipped or fails.
6.  **Video Processing**:
    - **Cutting**: Segments are cut based on analyzed timestamps.
    - **Cropping**: Video is resized to 1080x1920 (9:16). Face detection ensures the subject is framed.
    - **Captioning**: Captions are specialized (Burned-in) using FFmpeg/MoviePy based on the selected style.
7.  **Output**: Generated clips are saved to `backend/processed/` and served via static URL.
8.  **Post-Processing**:
    - **Regenerate**: User can adjust style/color/size and re-render a specific clip instantly.
    - **Share**: User submits credentials to post directly to platforms.

---

## 4. Project Layout & Architecture

The project is structured as a Monorepo with a Next.js Frontend and FastAPI Backend.

### **Frontend (`frontend/`)**
Built with **Next.js 14**, **Tailwind CSS**, and **React**.
- **`src/app/page.tsx`**: Landing page showcasing features and pricing/demo links.
- **`src/app/upload/page.tsx`**: The main application interface. Handles:
  - File/URL Input states.
  - Processing progress bar.
  - Advanced Settings (Accordion for colors/fonts).
  - Results display (Video Player, Regenerate & Share dialogs).
- **`src/components/`**: UI components (shadcn/ui), icons (Lucide), and overlays.

### **Backend (`backend/`)**
Built with **FastAPI** (Python).
- **`main.py`**: Application entry point, CORS configuration, and Static file mounting.
- **`api/routes/`**:
  - `upload.py`: Handles file upload to local storage.
  - `process.py`: Orchestrates the video processing pipeline (Download -> Transcribe -> Cut).
  - `share.py`: Logic for Instagram/YouTube APIs.
  - `rocket.py`: Generates social media metadata (Titles/Tags).
- **`services/`**:
  - `video_processing.py`: Core logic for FFmpeg/MoviePy operations (cutting, cropping, burning subtitles).
  - `transcription.py`: Wraps Whisper for audio-to-text.
  - `analysis.py`: Logic for identifying viral moments.
  - `downloader.py`: Handles YouTube downloads.
- **`processed/`**: Directory where final `.mp4` and `.srt` files are stored.
- **`uploads/`**: Directory for raw source files.

---

## 5. Technology Stack

- **Frontend**: Next.js (TypeScript), React, Tailwind CSS, Shadcn UI, Framer Motion (animations).
- **Backend**: Python, FastAPI, Uvicorn.
- **Video/Audio**: FFmpeg, MoviePy, OpenAI Whisper, yt-dlp.
- **AI/ML**: OpenAI GPT (for analysis), Faster-Whisper (transcription).
- **Utilities**: Pydantic (validation), Dotenv (config).

## 6. API Endpoints Summary

- `POST /api/upload`: Upload a video file.
- `POST /api/process`: Trigger the pipeline (requires `file_id` or `video_url`).
- `POST /api/process/regenerate`: Re-create a clip with new styles.
- `POST /api/share/{platform}`: Share a generated clip to Instagram/YouTube.
- `POST /api/rocket/generate`: Generate titles/captions/hashtags for a clip.

