#!/bin/bash

# Скрипт для мониторинга автоматического публикатора статей

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Активируем виртуальное окружение
source venv/bin/activate

echo "📊 Мониторинг автоматического публикатора статей"
echo "=================================================="

# Проверяем статус процесса
if pgrep -f "auto_publisher.py" > /dev/null; then
    PUBLISHER_PID=$(pgrep -f "auto_publisher.py")
    echo "✅ Публикатор запущен (PID: $PUBLISHER_PID)"
else
    echo "❌ Публикатор не запущен"
fi

echo ""

# Показываем статус базы данных
echo "📋 Статус базы данных:"
python auto_publisher.py --status

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
echo "   Публикация сейчас: python auto_publisher.py --publish-now"
