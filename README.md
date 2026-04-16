# GetCourse Video Pipeline
Автоматизированный пайплайн: видео-урок → транскрипция → цифровой конспект

## 📋 Описание
Полностью автоматизированный пайплайн для:
1. **Авторизации** на GetCourse через Playwright (headless)
2. **Перехвата** видео-потока (m3u8, mp4, Kinescope, Vimeo)
3. **Скачивания** видео через yt-dlp с сохранением cookies
4. **Транскрипции** с помощью Whisper large-v3 (русский язык)
5. **Создания конспекта** через Claude API с структурированием

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
playwright install
```

### 2. Настройка .env
```bash
# Уже настроено в .env файле:
GETCOURSE_EMAIL=your-email@example.com
GETCOURSE_PASSWORD=your-password
GETCOURSE_LESSON_URL=https://kartozschool.ru/pl/teach/control/lesson/view?id=...
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 3. Запуск пайплайна
```bash
python pipeline.py
```

## 📂 Структура файлов
```
./
├── .env                   # Переменные окружения
├── pipeline.py            # Основной скрипт
├── requirements.txt       # Зависимости
├── README.md             # Этот файл
└── output/
    ├── lesson_video.mp4   # Скачанное видео
    ├── transcript.txt     # Текстовая транскрипция
    ├── transcript.srt     # SRT с временными кодами
    ├── summary.md         # Цифровой конспект
    └── error.log          # Логи ошибок
```

## 🔧 Особенности реализации

### Авторизация и перехват видео
- Использует **Playwright** с `headless=False` для видимого браузера
- Автоматически логинится при редиректе на страницу входа
- Слушает все network requests/responses
- Ищет: `.m3u8`, `.mp4`, `kinescope.io`, `vimeo.com`
- Сохраняет скриншот и HTML при ошибке (debug_screenshot.png, debug_page.html)

### Загрузка видео
- **yt-dlp** с `--cookies-from-browser chrome` для сохранения сессии
- Резервный вариант: если прямой URL не найден, пытается скачать через GETCOURSE_LESSON_URL
- Таймаут: 600 сек (10 минут)

### Транскрипция
- **Whisper large-v3** -最современная модель
- Язык: русский (ru)
- Выходит в 2 форматах: `.txt` и `.srt`
- Показывает первые 500 символов для проверки

### Создание конспекта
- **Claude Sonnet 4.5** через Anthropic SDK
- Автоматическое разбиение на части (макс 80k символов, перекрытие 2k)
- Структурированный формат с эмодзи и секциями
- Подсчёт потраченных токенов

### Обработка ошибок
- Все ошибки логируются в `./output/error.log`
- Для DRM-защиты: встроенная инструкция для BlackHole/SoundFlower на macOS
- Рандомные задержки (1-3 сек) между действиями браузера

## 📊 Пример вывода

```
============================================================
FINAL REPORT
============================================================
📹 Video Duration: 45:32
📝 Transcript Length: 12,450 words
🧠 Claude Tokens Used: 28,450 (in: 24,200, out: 4,250)

📂 Output Files:
   ✓ lesson_video.mp4
   ✓ transcript.txt
   ✓ transcript.srt
   ✓ summary.md

All files saved to: /path/to/output
============================================================
```

## 🛡️ Требования macOS

- **Python 3.11+**
- **Apple Silicon (M-series)** поддерживается
- **FFmpeg** (для анализа видео): `brew install ffmpeg`
- **Chrome/Chromium** (для Playwright)

## 🚨 Решение проблем

### "Video URL not found after 30 sec"
→ Сохранены файлы: `debug_screenshot.png`, `debug_page.html`
→ Проверьте, что видео загружается в браузере вручную

### "yt-dlp failed to download"
→ Может быть DRM-защита
→ Следуйте инструкции в консоли для записи системного аудио (BlackHole)

### "Transcription failed"
→ Проверьте наличие ffmpeg: `which ffmpeg`
→ Убедитесь, что видео скачалось: `ls -lh output/lesson_video.mp4`

### "Claude API error"
→ Проверьте ANTHROPIC_API_KEY в .env
→ Убедитесь, что API ключ активен

## 📝 Лицензия
MIT
