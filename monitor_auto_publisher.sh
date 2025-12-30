#!/bin/bash

# Скрипт для мониторинга автоматического публикатора статей TheNextAI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Уникальное имя процесса для этого проекта
PROCESS_NAME="thenextai_publisher.py"

# Активируем виртуальное окружение
source venv/bin/activate

echo "📊 Мониторинг автоматического публикатора статей TheNextAI"
echo "============================================================"

# Проверяем статус процесса
if pgrep -f "$PROCESS_NAME" > /dev/null; then
    PUBLISHER_PID=$(pgrep -f "$PROCESS_NAME")
    echo "✅ Публикатор запущен (PID: $PUBLISHER_PID)"
else
    echo "❌ Публикатор не запущен"
fi

echo ""

# Показываем статус базы данных
echo "📋 Статус базы данных:"
python "$PROCESS_NAME" --status

echo ""

# Показываем последние логи
if [ -f "logs/auto_publisher.out" ]; then
    echo "📝 Последние записи в логах:"
    echo "----------------------------------------"
    tail -10 logs/auto_publisher.out
else
    echo "📝 Лог файл не найден"
fi

echo ""

# Показываем размер лог файла
if [ -f "logs/auto_publisher.out" ]; then
    LOG_SIZE=$(du -h logs/auto_publisher.out | cut -f1)
    echo "📏 Размер лог файла: $LOG_SIZE"
fi

echo ""
echo "🔧 Команды для управления:"
echo "   Запуск: ./start_auto_publisher.sh"
echo "   Остановка: ./stop_auto_publisher.sh"
echo "   Просмотр логов: tail -f logs/auto_publisher.out"
echo "   Публикация сейчас: python $PROCESS_NAME --publish-now"
