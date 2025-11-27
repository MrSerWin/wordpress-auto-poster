# Генерация видео через Gemini Veo API

## Быстрый старт

```bash
python generate_video.py "Your video prompt here"
```

Или интерактивный режим:
```bash
python generate_video.py
```

## Возможности

- ✅ Три модели на выбор:
  - `veo-2.0-generate-001` - стабильная версия
  - `veo-003-generate` - Veo 3, максимальное качество
  - `veo-003-generate-fast` - Veo 3, быстрая генерация

- ✅ Соотношения сторон:
  - 16:9 (горизонтальное)
  - 9:16 (вертикальное, для Instagram/TikTok)
  - 1:1 (квадрат)

- ✅ Разрешения:
  - 1080p (Full HD)
  - 720p (HD)
  - 480p

- ✅ Опциональная озвучка/narration

## Примеры

### Базовое использование
```bash
python generate_video.py "Futuristic AI robot working in modern office"
```

### С параметрами
Скрипт спросит интерактивно:
1. Выбор модели (1/2/3)
2. Соотношение сторон (1/2/3)
3. Разрешение (1/2/3)
4. Озвучка (y/n)

## Требования

- Google API Key в `.env` файле
- Доступ к Gemini Veo API (может требовать платную подписку)
- Python библиотеки: `google-genai`, `requests`, `python-dotenv`

## Примечания

- Генерация может занять несколько минут
- Видео сохраняется как `generated_video_YYYYMMDD_HHMMSS.mp4`
- Максимальное время ожидания: 30 минут
