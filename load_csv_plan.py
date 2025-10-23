#!/usr/bin/env python3
"""
Скрипт для загрузки плана статей из CSV файла в базу данных.
Поддерживает проверку дубликатов по заголовкам.
"""

import sqlite3
import csv
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Маппинг категорий на существующие на портале
CATEGORY_MAPPING = {
    'Culture': 'AI & Culture',
    'Society': 'AI & Society', 
    'Practice': 'AI Pro Tips / How-To',
    'Innovation': 'Innovation',
    'Review': 'Review',
    'News': 'News',
    'History': 'History',
    'Video': 'Video'
}

def map_category(category):
    """
    Мапит категорию на существующую на портале.
    
    Args:
        category (str): Исходная категория
        
    Returns:
        str: Маппированная категория или 'News' по умолчанию
    """
    return CATEGORY_MAPPING.get(category, 'News')

def load_csv_plan(csv_file_path):
    """
    Загружает план статей из CSV файла в базу данных.
    
    Args:
        csv_file_path (str): Путь к CSV файлу
        
    Returns:
        dict: Статистика загрузки
    """
    
    # Проверяем существование файла
    if not os.path.exists(csv_file_path):
        print(f"❌ Файл {csv_file_path} не найден!")
        return {"error": "File not found"}
    
    # Подключаемся к базе данных
    conn = sqlite3.connect('storage.db')
    cur = conn.cursor()
    
    # Создаем таблицу, если её нет
    cur.execute('''
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seed TEXT NOT NULL,
            seo_focus TEXT,
            created_at TEXT NOT NULL,
            last_published_at TEXT,
            status TEXT DEFAULT 'pending',
            category TEXT
        )
    ''')
    
    # Добавляем колонку category, если её нет
    try:
        cur.execute('ALTER TABLE plans ADD COLUMN category TEXT')
        print("✅ Добавлена колонка 'category' в таблицу plans")
    except sqlite3.OperationalError:
        # Колонка уже существует
        pass
    
    stats = {
        "total_rows": 0,
        "added": 0,
        "skipped_duplicates": 0,
        "errors": 0
    }
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            # Читаем файл построчно и обрабатываем каждую строку
            lines = file.readlines()
        
        for row_num, line in enumerate(lines, 1):
            stats["total_rows"] += 1
            
            # Пропускаем пустые строки
            line = line.strip()
            if not line:
                print(f"⚠️  Строка {row_num}: пропущена (пустая)")
                stats["errors"] += 1
                continue
            
            # Разделяем по первой запятой (категория, заголовок)
            if ',' not in line:
                print(f"⚠️  Строка {row_num}: пропущена (нет запятой)")
                stats["errors"] += 1
                continue
            
            # Находим первую запятую и разделяем
            comma_pos = line.find(',')
            original_category = line[:comma_pos].strip()
            title = line[comma_pos + 1:].strip()
            
            # Мапим категорию на существующую на портале
            category = map_category(original_category)
            
            # Проверяем на дубликаты по заголовку
            cur.execute('SELECT id FROM plans WHERE seed = ?', (title,))
            if cur.fetchone():
                print(f"⏭️  Строка {row_num}: пропущена (дубликат) - '{title[:50]}...'")
                stats["skipped_duplicates"] += 1
                continue
            
            # Добавляем в базу
            current_time = datetime.now(timezone.utc).isoformat()
            cur.execute('''
                INSERT INTO plans (seed, seo_focus, created_at, status, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, '', current_time, 'pending', category))
            
            # Показываем маппинг категории
            mapping_info = f"{original_category} → {category}" if original_category != category else category
            print(f"✅ Строка {row_num}: добавлена - '{title[:50]}...' (категория: {mapping_info})")
            stats["added"] += 1
        
        # Сохраняем изменения
        conn.commit()
        
    except Exception as e:
        print(f"❌ Ошибка при обработке файла: {e}")
        stats["errors"] += 1
        conn.rollback()
    
    finally:
        conn.close()
    
    return stats

def show_database_status():
    """Показывает текущий статус базы данных"""
    conn = sqlite3.connect('storage.db')
    cur = conn.cursor()
    
    print("\n📊 Статус базы данных:")
    
    # Общая статистика
    cur.execute('SELECT COUNT(*) FROM plans')
    total = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM plans WHERE status = "pending"')
    pending = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM plans WHERE status = "published"')
    published = cur.fetchone()[0]
    
    print(f"   Всего статей: {total}")
    print(f"   Ожидают публикации: {pending}")
    print(f"   Уже опубликованы: {published}")
    
    # Статистика по категориям (если колонка существует)
    try:
        cur.execute('SELECT category, COUNT(*) FROM plans GROUP BY category ORDER BY COUNT(*) DESC')
        categories = cur.fetchall()
        
        if categories:
            print(f"\n📂 Статистика по категориям:")
            for category, count in categories:
                print(f"   {category}: {count}")
    except sqlite3.OperationalError:
        # Колонка category еще не добавлена
        pass
    
    # Последние добавленные статьи
    try:
        cur.execute('SELECT seed, category, created_at FROM plans ORDER BY created_at DESC LIMIT 5')
        recent = cur.fetchall()
        
        if recent:
            print(f"\n📝 Последние добавленные статьи:")
            for title, category, created_at in recent:
                category_str = f" ({category})" if category else ""
                print(f"   {title[:60]}...{category_str} - {created_at[:10]}")
    except sqlite3.OperationalError:
        # Колонка category еще не добавлена, показываем без неё
        cur.execute('SELECT seed, created_at FROM plans ORDER BY created_at DESC LIMIT 5')
        recent = cur.fetchall()
        
        if recent:
            print(f"\n📝 Последние добавленные статьи:")
            for title, created_at in recent:
                print(f"   {title[:60]}... - {created_at[:10]}")
    
    conn.close()

def main():
    """Основная функция"""
    if len(sys.argv) != 2:
        print("📋 Использование: python load_csv_plan.py <путь_к_csv_файлу>")
        print("📋 Пример: python load_csv_plan.py plans/plan7-11.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    print(f"🚀 Загрузка плана статей из {csv_file}")
    print("=" * 60)
    
    # Показываем текущий статус
    show_database_status()
    
    print(f"\n📥 Загружаем статьи из {csv_file}...")
    print("-" * 60)
    
    # Загружаем CSV
    stats = load_csv_plan(csv_file)
    
    if "error" in stats:
        print(f"❌ Ошибка: {stats['error']}")
        sys.exit(1)
    
    # Показываем результаты
    print("\n" + "=" * 60)
    print("📊 Результаты загрузки:")
    print(f"   Всего строк обработано: {stats['total_rows']}")
    print(f"   ✅ Добавлено новых статей: {stats['added']}")
    print(f"   ⏭️  Пропущено дубликатов: {stats['skipped_duplicates']}")
    print(f"   ❌ Ошибок: {stats['errors']}")
    
    # Показываем обновленный статус
    show_database_status()
    
    print("\n✅ Загрузка завершена!")

if __name__ == "__main__":
    main()
