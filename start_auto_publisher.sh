#!/bin/bash

# Скрипт для запуска автоматического публикатора статей
# Запускает публикатор в фоновом режиме с логированием

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Активируем виртуальное окружение
source venv/bin/activate

# Проверяем, не запущен ли уже публикатор
if pgrep -f "auto_publisher.py" > /dev/null; then
    echo "❌ Автоматический публикатор уже запущен"
    echo "   PID: $(pgrep -f "auto_publisher.py")"
    echo "   Для остановки: pkill -f auto_publisher.py"
    exit 1
fi

# Создаем директорию для логов
mkdir -p logs

# Запускаем публикатор в фоновом режиме
echo "🚀 Запускаем автоматический публикатор статей..."
nohup python auto_publisher.py > logs/auto_publisher.out 2>&1 &

# Получаем PID процесса
PUBLISHER_PID=$!

# Сохраняем PID в файл
echo $PUBLISHER_PID > logs/auto_publisher.pid

echo "✅ Автоматический публикатор запущен"
echo "   PID: $PUBLISHER_PID"
echo "   Логи: logs/auto_publisher.out"
echo "   PID файл: logs/auto_publisher.pid"
echo ""
echo "📋 Команды для управления:"
echo "   Просмотр логов: tail -f logs/auto_publisher.out"
echo "   Остановка: pkill -f auto_publisher.py"
echo "   Статус: python auto_publisher.py --status"
echo "   Публикация сейчас: python auto_publisher.py --publish-now"
