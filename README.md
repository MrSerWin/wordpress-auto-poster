# AutoPoster — WordPress Auto Publisher с интеграцией Gemini AI

Приложение для автоматической публикации статей на WordPress с использованием искусственного интеллекта (Gemini) для генерации контента и изображений.

## Основные возможности

- Автоматическая генерация статей с помощью Gemini AI
- Генерация изображений для статей
- Публикация на WordPress через REST API
- Планировщик для периодической публикации
- SEO-оптимизация контента
- REST API для управления публикациями

## Структура проекта

- `main.py` — FastAPI сервер + планировщик публикаций
- `gemini_client.py` — клиент для работы с Gemini/Google GenAI
- `wordpress_client.py` — загрузка медиа и создание постов через WordPress REST API
- `requirements.txt` — зависимости проекта
- `.env` — переменные окружения (не коммитить!)
- `run.sh` — скрипт для запуска приложения

## Быстрый старт

### 1. Установка и настройка

```bash
# Клонируйте репозиторий и перейдите в папку
cd wordpress-auto-poster

# Создайте файл .env с вашими настройками
cat > .env << EOF
GOOGLE_API_KEY=your_google_api_key
WP_BASE_URL=https://your-site.com
WP_USERNAME=your_wp_username
WP_APP_PASSWORD=your_application_password
PUBLISH_INTERVAL_DAYS=3
EOF
```

### 2. Настройка WordPress Application Password

**ВАЖНО:** Для работы с WordPress REST API нужен Application Password (не обычный пароль от админки!)

1. Зайдите в WordPress Admin: `https://your-site.com/wp-admin`
2. Перейдите: **Users → Profile** (или **Users → [ваш-пользователь]**)
3. Прокрутите вниз до секции **"Application Passwords"**
4. Введите название (например, "Auto Poster") и нажмите **"Add New Application Password"**
5. **Скопируйте сгенерированный пароль** (показывается только один раз!)
6. Используйте этот пароль в `.env` файле (можно с пробелами или без)

### 3. Запуск приложения

```bash
# Простой запуск через скрипт
./run.sh

# Или вручную:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Сервер будет доступен по адресу: http://127.0.0.1:8000

API документация: http://127.0.0.1:8000/docs

## API Endpoints

### `POST /generate`
Генерирует и публикует статью немедленно

```bash
curl -X POST http://127.0.0.1:8000/generate
```

Ответ:
```json
{
  "message": "Article published successfully!",
  "post_id": 190,
  "link": "https://your-site.com/post-slug/",
  "featured_image": 189
}
```

### `POST /plan`
Добавляет план статьи для будущей публикации

```bash
curl -X POST http://127.0.0.1:8000/plan \
  -H "Content-Type: application/json" \
  -d '{"seed": "Искусственный интеллект в медицине", "seo_focus": "AI healthcare"}'
```

### `POST /publish-now`
Запускает публикацию следующей запланированной статьи

```bash
curl -X POST http://127.0.0.1:8000/publish-now
```

### `GET /status`
Проверяет статус приложения и количество опубликованных статей

```bash
curl http://127.0.0.1:8000/status
```

## Устранение проблем

### Ошибка 401 Unauthorized

Если получаете ошибку аутентификации:

1. **Проверьте Application Password** - это НЕ обычный пароль от админки
2. **Создайте новый Application Password** в WordPress (см. инструкцию выше)
3. **Обновите `.env` файл** с новым паролем
4. **Перезапустите приложение** - важно, чтобы не было переменных окружения в shell

```bash
# Очистите переменные окружения и перезапустите
unset WP_APP_PASSWORD WP_USERNAME WP_BASE_URL
./run.sh
```

### Тестирование аутентификации

Используйте встроенные скрипты для диагностики:

```bash
# Полная диагностика WordPress
python diagnose_wp.py

# Тест аутентификации
python test_wp_auth.py

# Интерактивная настройка пароля
python setup_wp_password.py
```

## Важные замечания

- **Application Password ≠ обычный пароль** - создавайте отдельный пароль для API
- **Не коммитьте `.env`** файл в git (добавлен в `.gitignore`)
- **Пароль без кавычек** - в `.env` не используйте кавычки вокруг значений
- **HTTPS обязателен** - Application Passwords работают только по HTTPS
- **Права пользователя** - пользователь должен иметь роль Editor или Administrator

## Требования

- Python 3.8+
- macOS (или Linux/Windows с небольшими изменениями)
- WordPress 5.6+ с включенными Application Passwords
- HTTPS на WordPress сайте
- Google Gemini API ключ

