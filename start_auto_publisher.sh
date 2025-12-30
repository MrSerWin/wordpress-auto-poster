#!/bin/bash

# Скрипт для запуска автоматического публикатора статей TheNextAI
# Запускает публикатор в фоновом режиме с логированием

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Уникальное имя процесса для этого проекта
PROCESS_NAME="thenextai_publisher.py"

# Активируем виртуальное окружение
source venv/bin/activate

# Проверяем, не запущен ли уже публикатор
if pgrep -f "$PROCESS_NAME" > /dev/null; then
    echo "❌ Автоматический публикатор уже запущен"
    echo "   PID: $(pgrep -f "$PROCESS_NAME")"
    echo "   Для остановки: ./stop_auto_publisher.sh"
    exit 1
fi

# Создаем директорию для логов
mkdir -p logs

# Запускаем публикатор в фоновом режиме
echo "🚀 Запускаем автоматический публикатор статей TheNextAI..."
nohup python "$PROCESS_NAME" > logs/auto_publisher.out 2>&1 &

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
echo "   Остановка: ./stop_auto_publisher.sh"
echo "   Статус: python $PROCESS_NAME --status"
echo "   Публикация сейчас: python $PROCESS_NAME --publish-now"
