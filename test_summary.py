#!/usr/bin/env python3
"""Quick test of summary generation from existing transcript"""

import os
import sys
from pathlib import Path
from anthropic import Anthropic

# Load .env
from dotenv import load_dotenv
load_dotenv()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
OUTPUT_DIR = Path('./output')

def generate_summary(transcript: str):
    """Generate summary using Claude"""
    client = Anthropic()

    PROMPT = """Ты эксперт по созданию учебных материалов.
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
"""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": PROMPT + transcript
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

if __name__ == "__main__":
    transcript_file = OUTPUT_DIR / 'transcript.txt'
    
    if not transcript_file.exists():
        print(f"Transcript not found at {transcript_file}")
        sys.exit(1)

    print("Reading transcript...")
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript = f.read()

    word_count = len(transcript.split())
    print(f"Transcript loaded: {word_count} words")
    print("\nGenerating summary with Claude...")

    try:
        summary, usage = generate_summary(transcript)

        # Save summary
        summary_file = OUTPUT_DIR / 'summary.md'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)

        print(f"\n{'='*60}")
        print(f"SUMMARY GENERATED SUCCESSFULLY")
        print(f"{'='*60}")
        print(f"📝 Transcript: {word_count} words")
        print(f"🧠 Claude Tokens: {usage['total_tokens']:,}")
        print(f"   Input: {usage['input_tokens']:,} | Output: {usage['output_tokens']:,}")
        print(f"📄 Output: {summary_file.absolute()}")
        print(f"\nPreview:")
        print("-" * 60)
        print(summary[:1000] + "\n...")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
