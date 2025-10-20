#!/bin/bash

# Скрипт для остановки автоматического публикатора статей

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛑 Останавливаем автоматический публикатор статей..."

# Проверяем, запущен ли публикатор
if ! pgrep -f "auto_publisher.py" > /dev/null; then
    echo "❌ Автоматический публикатор не запущен"
    exit 1
fi

# Получаем PID
PUBLISHER_PID=$(pgrep -f "auto_publisher.py")
echo "   Найден процесс с PID: $PUBLISHER_PID"

# Останавливаем процесс
pkill -f "auto_publisher.py"

# Ждем завершения
sleep 2

# Проверяем, остановился ли процесс
if pgrep -f "auto_publisher.py" > /dev/null; then
    echo "⚠️  Процесс не остановился, принудительно завершаем..."
    pkill -9 -f "auto_publisher.py"
    sleep 1
fi

# Удаляем PID файл
if [ -f "logs/auto_publisher.pid" ]; then
    rm logs/auto_publisher.pid
fi

echo "✅ Автоматический публикатор остановлен"
