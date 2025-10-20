# Автоматический публикатор статей

Система автоматической генерации и публикации статей на WordPress каждые 3 дня.

## 🚀 Быстрый старт

### 1. Загрузка плана статей
```bash
# Загрузить статьи из plan.txt в базу данных
python load_plan.py

# Показать статус плана
python load_plan.py --status
```

### 2. Запуск автоматического публикатора
```bash
# Запустить в фоновом режиме
./start_auto_publisher.sh

# Проверить статус
./monitor_auto_publisher.sh

# Остановить
./stop_auto_publisher.sh
```

## 📋 Управление

### Команды для работы с планом
```bash
# Загрузить план статей
python load_plan.py

# Показать статус плана
python load_plan.py --status
```

### Команды для публикатора
```bash
# Показать статус системы
python auto_publisher.py --status

# Опубликовать статью сейчас
python auto_publisher.py --publish-now

# Запустить в режиме демона (вручную)
python auto_publisher.py
```

### Скрипты управления
```bash
# Запуск в фоновом режиме
./start_auto_publisher.sh

# Мониторинг
./monitor_auto_publisher.sh

# Остановка
./stop_auto_publisher.sh
```

## 📊 Мониторинг

### Просмотр логов
```bash
# Просмотр логов в реальном времени
tail -f logs/auto_publisher.out

# Последние 50 строк
tail -50 logs/auto_publisher.out
```

### Проверка статуса
```bash
# Полный статус
./monitor_auto_publisher.sh

# Только статус базы данных
python auto_publisher.py --status
```

## 🗄️ База данных

Система использует SQLite базу данных `storage.db` с таблицами:

### Таблица `plans`
- `id` - уникальный идентификатор
- `seed` - заголовок статьи
- `seo_focus` - SEO фокус
- `created_at` - дата создания
- `last_published_at` - дата публикации
- `status` - статус ('pending' или 'published')

### Таблица `posts`
- `id` - уникальный идентификатор
- `title` - заголовок поста
- `slug` - URL слаг
- `wp_id` - ID в WordPress
- `published_at` - дата публикации
- `seo_keywords` - ключевые слова

## ⚙️ Настройки

### Интервал публикации
По умолчанию статьи публикуются каждые 3 дня. Для изменения отредактируйте переменную `PUBLISH_INTERVAL_DAYS` в файле `auto_publisher.py`.

### Логика работы планировщика
- **При первом запуске**: Если в базе данных нет опубликованных статей, система сразу опубликует первую статью
- **При повторном запуске**: Система проверяет время последней публикации из базы данных и публикует следующую статью только если прошло 3 дня
- **Проверка каждые 5 минут**: Система проверяет, не пора ли публиковать статью
- **Статус каждые 6 часов**: В логах отображается текущий статус системы

### Логирование
Логи сохраняются в файл `auto_publisher.log` и выводятся в консоль.

## 🔧 Устранение неполадок

### Публикатор не запускается
```bash
# Проверить, не запущен ли уже
ps aux | grep auto_publisher

# Остановить все процессы
pkill -f auto_publisher.py

# Запустить заново
./start_auto_publisher.sh
```

### Ошибки в логах
```bash
# Просмотр ошибок
grep -i error logs/auto_publisher.out

# Просмотр последних ошибок
tail -100 logs/auto_publisher.out | grep -i error
```

### Проблемы с базой данных
```bash
# Проверить базу данных
sqlite3 storage.db ".tables"
sqlite3 storage.db "SELECT COUNT(*) FROM plans WHERE status='pending';"
```

## 📁 Структура файлов

```
wordpress-auto-poster/
├── auto_publisher.py          # Основной скрипт публикатора
├── load_plan.py              # Загрузка плана статей
├── start_auto_publisher.sh   # Скрипт запуска
├── stop_auto_publisher.sh    # Скрипт остановки
├── monitor_auto_publisher.sh # Скрипт мониторинга
├── plan.txt                  # План статей
├── storage.db                # База данных SQLite
├── logs/                     # Директория логов
│   ├── auto_publisher.out    # Логи публикатора
│   └── auto_publisher.pid    # PID файл
└── generated_images/         # Сгенерированные изображения
```

## 🎯 Примеры использования

### Добавление новых статей в план
1. Отредактируйте файл `plan.txt`
2. Запустите `python load_plan.py`
3. Новые статьи будут добавлены в очередь

### Публикация статьи вручную
```bash
python auto_publisher.py --publish-now
```

### Проверка работы системы
```bash
# Полный мониторинг
./monitor_auto_publisher.sh

# Только статус
python auto_publisher.py --status
```

## 🔄 Автоматический запуск при загрузке системы

Для автоматического запуска при загрузке системы добавьте в crontab:

```bash
# Редактировать crontab
crontab -e

# Добавить строку для запуска при загрузке
@reboot cd /path/to/wordpress-auto-poster && ./start_auto_publisher.sh
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `tail -f logs/auto_publisher.out`
2. Проверьте статус: `./monitor_auto_publisher.sh`
3. Перезапустите систему: `./stop_auto_publisher.sh && ./start_auto_publisher.sh`
