#!/usr/bin/env python3
"""
GetCourse Video → Transcript → Digital Summary Pipeline
Автоматизированный пайплайн: видео-урок → транскрипция → цифровой конспект
"""

import os
import sys
import json
import time
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse
import subprocess
import random

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, Browser
from anthropic import Anthropic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('./output/error.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GETCOURSE_EMAIL = os.getenv('GETCOURSE_EMAIL')
GETCOURSE_PASSWORD = os.getenv('GETCOURSE_PASSWORD')
GETCOURSE_LESSON_URL = os.getenv('GETCOURSE_LESSON_URL')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Create output directory
OUTPUT_DIR = Path('./output')
OUTPUT_DIR.mkdir(exist_ok=True)

class GetCourseVideoExtractor:
    """Extract video URL from GetCourse lesson page"""

    def __init__(self):
        self.video_url = None
        self.video_duration = None
        self.captured_requests = []

    async def extract_video_url(self) -> Optional[str]:
        """Extract video URL from GetCourse using Playwright"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            # Setup request/response listeners
            page.on("request", self._on_request)
            page.on("response", self._on_response)

            try:
                logger.info(f"Opening GetCourse lesson: {GETCOURSE_LESSON_URL}")
                await page.goto(GETCOURSE_LESSON_URL, wait_until="networkidle")

                # Check if login is required
                if "login" in page.url.lower():
                    logger.info("Login required, attempting authentication...")
                    await self._login(page)

                # Wait for video to load
                logger.info("Waiting for video to load...")
                start_time = time.time()
                while not self.video_url and (time.time() - start_time) < 30:
                    # Add random delay between actions
                    await page.wait_for_timeout(random.randint(1000, 3000))

                if not self.video_url:
                    logger.warning("Video URL not found in network requests, saving debug info...")
                    await self._save_debug_info(page)

                await browser.close()
                return self.video_url

            except Exception as e:
                logger.error(f"Error extracting video: {e}")
                await browser.close()
                return None

    async def _login(self, page: Page) -> None:
        """Authenticate to GetCourse"""
        try:
            # Wait for email input and fill it
            await page.wait_for_selector('input[type="email"]', timeout=10000)
            await page.fill('input[type="email"]', GETCOURSE_EMAIL)
            await page.wait_for_timeout(random.randint(1000, 2000))

            # Fill password
            password_input = await page.query_selector('input[type="password"]')
            if password_input:
                await page.fill('input[type="password"]', GETCOURSE_PASSWORD)
                await page.wait_for_timeout(random.randint(1000, 2000))

            # Submit form
            submit_btn = await page.query_selector('button[type="submit"]')
            if submit_btn:
                await submit_btn.click()
                await page.wait_for_navigation()
                logger.info("Authentication successful")

        except Exception as e:
            logger.error(f"Login error: {e}")

    def _on_request(self, request) -> None:
        """Capture all requests"""
        self.captured_requests.append(request.url)
        logger.debug(f"Request: {request.url}")

    def _on_response(self, response) -> None:
        """Capture video URLs from responses"""
        url = response.url

        # Look for video streaming URLs
        if any(pattern in url for pattern in ['.m3u8', '.mp4', 'kinescope.io', 'vimeo.com', 'wistia']):
            logger.info(f"Found video URL: {url}")
            self.video_url = url

    async def _save_debug_info(self, page: Page) -> None:
        """Save debug information for troubleshooting"""
        try:
            screenshot_path = OUTPUT_DIR / 'debug_screenshot.png'
            html_path = OUTPUT_DIR / 'debug_page.html'

            await page.screenshot(path=str(screenshot_path))
            html_content = await page.content()

            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"Debug info saved: {screenshot_path}, {html_path}")
            logger.info(f"Captured requests: {json.dumps(self.captured_requests[:10], indent=2)}")

        except Exception as e:
            logger.error(f"Error saving debug info: {e}")


class VideoDownloader:
    """Download video using yt-dlp"""

    @staticmethod
    def download_video(video_url: Optional[str] = None, lesson_url: str = None) -> bool:
        """Download video using yt-dlp"""
        output_file = OUTPUT_DIR / 'lesson_video.mp4'

        try:
            # Try with video URL first
            if video_url:
                logger.info(f"Downloading from direct URL: {video_url}")
                url_to_download = video_url
            else:
                logger.info(f"Downloading from lesson URL: {lesson_url}")
                url_to_download = lesson_url

            cmd = [
                'yt-dlp',
                '--cookies-from-browser', 'chrome',
                '-f', 'best',
                '-o', str(output_file),
                url_to_download
            ]

            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                logger.info(f"Video downloaded successfully: {output_file}")
                return True
            else:
                logger.error(f"yt-dlp error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Video download timeout (600s)")
            return False
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False


class WhisperTranscriber:
    """Transcribe audio using Whisper"""

    @staticmethod
    def transcribe(video_file: Path) -> Optional[str]:
        """Transcribe video using Whisper large-v3"""
        try:
            import whisper

            logger.info(f"Starting transcription with Whisper large-v3: {video_file}")
            model = whisper.load_model("large-v3")

            result = model.transcribe(
                str(video_file),
                language="ru",
                task="transcribe"
            )

            transcript = result["text"]

            # Save as TXT
            txt_file = OUTPUT_DIR / 'transcript.txt'
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
            logger.info(f"Transcript saved: {txt_file}")

            # Save as SRT
            srt_file = OUTPUT_DIR / 'transcript.srt'
            WhisperTranscriber._save_srt(result, srt_file)
            logger.info(f"SRT saved: {srt_file}")

            # Print preview
            preview = transcript[:500]
            logger.info(f"\n{'='*60}\nTRANSCRIPT PREVIEW:\n{'='*60}\n{preview}...\n{'='*60}\n")

            return transcript

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None

    @staticmethod
    def _save_srt(result: dict, output_file: Path) -> None:
        """Save transcript as SRT format"""
        try:
            srt_content = ""
            index = 1

            for segment in result.get("segments", []):
                start = WhisperTranscriber._seconds_to_srt_time(segment["start"])
                end = WhisperTranscriber._seconds_to_srt_time(segment["end"])
                text = segment["text"].strip()

                srt_content += f"{index}\n{start} --> {end}\n{text}\n\n"
                index += 1

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(srt_content)

        except Exception as e:
            logger.error(f"Error saving SRT: {e}")

    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """Convert seconds to SRT time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class ClaudeSummaryGenerator:
    """Generate digital summary using Claude API"""

    SUMMARY_PROMPT = """Ты эксперт по созданию учебных материалов.
На основе транскрипта видео-урока создай структурированный цифровой конспект на русском языке.

Структура конспекта:
# [Название темы урока]

## 🎯 Главная идея (1-2 предложения)

## 📚 Ключевые концепции
- Термин/понятие: краткое определение

## 📝 Основные тезисы
(нумерованный список, каждый тезис 1-2 предложения)

## 💡 Примеры и кейсы
(конкретные примеры из урока)

## ⚡ Практические выводы
(что нужно сделать / применить)

## ❓ Вопросы для самопроверки
(3-5 вопросов по материалу)

Транскрипт:
{transcript}"""

    MAX_CHUNK_SIZE = 80000
    CHUNK_OVERLAP = 2000

    @staticmethod
    def generate_summary(transcript: str) -> Tuple[str, dict]:
        """Generate summary using Claude, handling long transcripts"""
        client = Anthropic()

        # Split transcript if needed
        chunks = ClaudeSummaryGenerator._split_transcript(transcript)

        if len(chunks) == 1:
            logger.info("Generating summary for single chunk...")
            summary, usage = ClaudeSummaryGenerator._process_chunk(
                client, chunks[0], is_multi=False
            )
        else:
            logger.info(f"Generating summaries for {len(chunks)} chunks...")
            summaries = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}...")
                chunk_summary, _ = ClaudeSummaryGenerator._process_chunk(
                    client, chunk, is_multi=True, chunk_num=i+1, total_chunks=len(chunks)
                )
                summaries.append(chunk_summary)

            # Combine chunks
            combined = "\n\n".join(summaries)
            summary, usage = ClaudeSummaryGenerator._process_chunk(
                client, combined, is_multi=False, final_merge=True
            )

        # Save summary
        summary_file = OUTPUT_DIR / 'summary.md'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        logger.info(f"Summary saved: {summary_file}")

        return summary, usage

    @staticmethod
    def _split_transcript(transcript: str) -> list:
        """Split long transcript into chunks"""
        if len(transcript) <= ClaudeSummaryGenerator.MAX_CHUNK_SIZE:
            return [transcript]

        chunks = []
        words = transcript.split()
        current_chunk = []
        current_size = 0

        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1

            if current_size >= ClaudeSummaryGenerator.MAX_CHUNK_SIZE:
                chunks.append(' '.join(current_chunk))
                # Add overlap
                overlap_words = int(ClaudeSummaryGenerator.CHUNK_OVERLAP / 5)
                current_chunk = current_chunk[-overlap_words:]
                current_size = sum(len(w) + 1 for w in current_chunk)

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    @staticmethod
    def _process_chunk(client, transcript_chunk: str, is_multi: bool = False,
                      chunk_num: int = None, total_chunks: int = None,
                      final_merge: bool = False) -> Tuple[str, dict]:
        """Process a transcript chunk"""

        if final_merge:
            prompt = f"""Объедини следующие конспекты в один полный и структурированный конспект.
Сохрани все ключевые идеи и примеры:

{transcript_chunk}"""
        elif is_multi:
            prompt = f"""Создай конспект для части {chunk_num}/{total_chunks} видео-урока.
Фокусируйся на главных идеях и ключевых концепциях.

Транскрипт части:
{transcript_chunk}"""
        else:
            prompt = ClaudeSummaryGenerator.SUMMARY_PROMPT.format(transcript=transcript_chunk)

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        summary = response.content[0].text
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens
        }

        return summary, usage


class Pipeline:
    """Main pipeline orchestrator"""

    async def run(self) -> None:
        """Run the complete pipeline"""
        try:
            logger.info("="*60)
            logger.info("GetCourse → Transcript → Summary Pipeline Started")
            logger.info("="*60)

            # Step 1: Extract video URL
            logger.info("\n[STEP 1] Extracting video URL from GetCourse...")
            extractor = GetCourseVideoExtractor()
            video_url = await extractor.extract_video_url()

            # Step 2: Download video
            logger.info("\n[STEP 2] Downloading video...")
            video_file = OUTPUT_DIR / 'lesson_video.mp4'

            if not VideoDownloader.download_video(video_url, GETCOURSE_LESSON_URL):
                if not video_url:
                    logger.error("Could not extract video URL and download failed")
                    logger.error("For DRM-protected content, try recording system audio:")
                    print(self._get_audio_recording_instructions())
                    return

            # Step 3: Transcribe
            logger.info("\n[STEP 3] Transcribing with Whisper...")
            transcript = WhisperTranscriber.transcribe(video_file)

            if not transcript:
                logger.error("Transcription failed")
                return

            # Step 4: Generate summary
            logger.info("\n[STEP 4] Generating digital summary with Claude...")
            summary, usage = ClaudeSummaryGenerator.generate_summary(transcript)

            # Step 5: Final report
            logger.info("\n[STEP 5] Pipeline complete!")
            self._print_final_report(video_file, transcript, usage)

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)

    @staticmethod
    def _print_final_report(video_file: Path, transcript: str, usage: dict) -> None:
        """Print final report"""
        word_count = len(transcript.split())

        # Get video duration
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1:noprint_wrappers=1',
                 str(video_file)],
                capture_output=True, text=True, timeout=30
            )
            duration = float(result.stdout.strip())
            duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}"
        except:
            duration_str = "Unknown"

        report = f"""
{'='*60}
FINAL REPORT
{'='*60}
📹 Video Duration: {duration_str}
📝 Transcript Length: {word_count:,} words
🧠 Claude Tokens Used: {usage['total_tokens']:,} (in: {usage['input_tokens']:,}, out: {usage['output_tokens']:,})

📂 Output Files:
   ✓ {video_file.name}
   ✓ {(OUTPUT_DIR / 'transcript.txt').name}
   ✓ {(OUTPUT_DIR / 'transcript.srt').name}
   ✓ {(OUTPUT_DIR / 'summary.md').name}

All files saved to: {OUTPUT_DIR.absolute()}
{'='*60}
"""
        logger.info(report)
        print(report)

    @staticmethod
    def _get_audio_recording_instructions() -> str:
        """Get instructions for recording protected video audio"""
        return """
DRM-PROTECTED CONTENT - Audio Recording Instructions
=====================================================

For macOS, use one of these methods to record system audio:

Method 1: BlackHole (recommended)
1. Install BlackHole: brew install blackhole-2ch
2. In System Settings → Sound → Output → Select "BlackHole 2ch"
3. Open the video in browser
4. Run: ffmpeg -f avfoundation -i ":BlackHole 2ch" -t <duration> audio.m4a
5. Then: ffmpeg -i video.mp4 -i audio.m4a -c:v copy output.mp4

Method 2: SoundFlower
1. Install: brew install soundflower
2. Set as output device
3. Record with ffmpeg using avfoundation

After getting audio.m4a, run:
whisper audio.m4a --language ru --output_format txt,srt --model large-v3
"""


async def main():
    """Main entry point"""
    if not all([GETCOURSE_EMAIL, GETCOURSE_PASSWORD, GETCOURSE_LESSON_URL, ANTHROPIC_API_KEY]):
        logger.error("Missing required environment variables in .env")
        sys.exit(1)

    pipeline = Pipeline()
    await pipeline.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
