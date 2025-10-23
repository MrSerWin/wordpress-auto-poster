# 📋 Инструкция по загрузке статей из CSV

## Быстрый старт

### 1. Подготовка CSV файла
Создайте CSV файл с двумя колонками:
- **Колонка 1**: Категория статьи
- **Колонка 2**: Заголовок статьи

### 2. Загрузка в базу данных
```bash
python load_csv_plan.py plans/your_plan.csv
```

### 3. Проверка результата
```bash
./monitor_auto_publisher.sh
```

## Пример CSV файла

```csv
Innovation,The Rise of Multimodal AI: Beyond Text and Image
Society,The New Regulator: How Global Governments Are Taming the AI Beast
Practice,Mastering Multimodal Prompts: A Practical Guide
Review,AI in the Cosmos: Exploring Space with Machine Learning
Culture,Creative Control vs. Automation: A Deep Dive into AI's Role
```

## Команды

| Команда | Описание |
|---------|----------|
| `python load_csv_plan.py plans/plan.csv` | Загрузить статьи из CSV |
| `./monitor_auto_publisher.sh` | Проверить статус системы |
| `./start_auto_publisher.sh` | Запустить автоматический публикатор |
| `./stop_auto_publisher.sh` | Остановить публикатор |

## Особенности

- ✅ **Проверка дубликатов** - одинаковые заголовки не добавляются повторно
- ✅ **Безопасность** - существующие данные не удаляются
- ✅ **Автоматическое создание колонки category** - при первом запуске
- ✅ **Поддержка различных разделителей** - запятая, точка с запятой, табуляция

## Текущий статус

- 📊 **Всего статей в базе**: 22
- ⏳ **Ожидают публикации**: 22
- ✅ **Уже опубликованы**: 0
- 📅 **Следующая публикация**: 26 октября 2025 в 16:13

## Категории статей

- **Innovation** - инновационные технологии
- **Society** - социальные аспекты ИИ
- **Practice** - практические руководства
- **Review** - обзоры и анализ
- **Culture** - культурные аспекты
- **News** - новости и анонсы
