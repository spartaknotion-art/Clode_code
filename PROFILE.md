# КТО Я

Основатель AI-компании, базирующейся в России. В команде двое живых людей — 
все остальные сотрудники — AI-агенты. Строю первый AI-only бизнес в РФ 
с целью капитализации $100 млн.

Бюджет: $30–50k на 6–12 месяцев.
Цель: $2–3k/мес к середине 2026, затем $10k+/мес.

---

## ЧЕМ ЗАНИМАЮСЬ

### Продукт 1 (готов)
Голосовой ассистент для медицинских клиник — pre-appointment AI.

### Продукт 2 (в разработке)
Система транскрибации и автоматического анализа медицинских анализов.

### Продукт 3 (активная разработка — ПРИОРИТЕТ)
AI-система полного цикла ведения социальных сетей (AI-SMM):
- Экстракция и воспроизведение стиля и «голоса» автора
- Генерация постов, Reels/Shorts/TikTok, ответы на комментарии
- Платформы: TikTok, YouTube, Instagram, ВКонтакте, Дзен
- Заменяет: маркетолога, копирайтера, SMM-щика, дизайнера, монтажёра
- Полный цикл: пре-продакшн → публикация → аналитика
- Интерфейс с клиентом через Telegram/Max

---

## ТЕХНИЧЕСКИЙ СТЕК

**Оркестрация:** n8n (self-hosted EU VPS), LangGraph, CrewAI, Dify  
**Агентные фреймворки:** LangGraph (production), CrewAI (прототипы)  
**AI-модели:** Claude Opus/Sonnet/Haiku, GPT-4o-mini, Gemini 2.5 Flash  
**Локальные LLM:** Qwen 3.5, Mistral, Llama 4 — через Ollama/LM Studio на Apple Silicon  
**Видеогенерация:** Kling, HeyGen, Runway  
**TTS/транскрибация:** Whisper  
**Парсинг:** Firecrawl, Apify, Playwright  
**Соцсети:** VK API, Telegram Bot API, Meta Graph API, TikTok for Developers  
**Мониторинг:** Langfuse (self-hosted)  
**Инфраструктура:** EU VPS (Hetzner/Contabo) — все AI API-запросы идут через VPS  
**QA:** DeepEval  

---

## КЛЮЧЕВОЕ ОГРАНИЧЕНИЕ

Компания в РФ. Claude, ChatGPT, Gemini блокируют российские IP.
Все production API-вызовы идут через EU VPS, а не напрямую из РФ.

---

## ПРАВИЛО ПРОТОТИП → PRODUCTION

- Прототип → Claude Team / Perplexity Space (часы)
- MVP → n8n + Dify self-hosted на EU VPS (дни)
- Production → LangGraph + self-hosted + локальные модели (недели)
