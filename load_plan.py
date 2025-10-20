#!/usr/bin/env python3
"""
Скрипт для загрузки плана статей из plan.txt в базу данных
"""

import sqlite3
import re
from datetime import datetime
import os

DB_FILE = 'storage.db'

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seed TEXT,
        seo_focus TEXT,
        created_at TEXT,
        last_published_at TEXT,
        status TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        slug TEXT,
        wp_id INTEGER,
        published_at TEXT,
        seo_keywords TEXT
    )""")
    conn.commit()
    conn.close()

def parse_plan_file(filename='plan.txt'):
    """Парсинг файла plan.txt и извлечение статей"""
    articles = []
    
    if not os.path.exists(filename):
        print(f"❌ Файл {filename} не найден")
        return articles
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем статьи по паттерну "Статья XX: Заголовок"
    pattern = r'Статья\s+\d+\s*\([^)]+\):\s*(.+?)(?=\n|$)'
    matches = re.findall(pattern, content, re.MULTILINE)
    
    for match in matches:
        title = match.strip()
        if title:
            articles.append({
                'title': title,
                'seo_focus': title  # Используем заголовок как SEO фокус
            })
    
    return articles

def add_article_to_db(title, seo_focus):
    """Добавление статьи в базу данных, если она еще не существует"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Проверяем, не существует ли уже такая статья
    cur.execute("SELECT id FROM plans WHERE seed = ?", (title,))
    existing = cur.fetchone()
    
    if existing:
        print(f"⚠️  Статья уже существует в базе: {title[:50]}...")
        conn.close()
        return False
    
    # Добавляем новую статью
    cur.execute('INSERT INTO plans (seed, seo_focus, created_at, status) VALUES (?, ?, ?, ?)',
                (title, seo_focus, datetime.utcnow().isoformat(), 'pending'))
    conn.commit()
    conn.close()
    
    print(f"✅ Добавлена статья: {title[:50]}...")
    return True

def load_plan_to_db():
    """Основная функция для загрузки плана в базу данных"""
    print("🚀 Загружаем план статей в базу данных...")
    
    # Инициализируем базу данных
    init_db()
    
    # Парсим файл плана
    articles = parse_plan_file()
    
    if not articles:
        print("❌ Не найдено статей в файле plan.txt")
        return
    
    print(f"📝 Найдено {len(articles)} статей в плане")
    
    # Добавляем статьи в базу данных
    added_count = 0
    for article in articles:
        if add_article_to_db(article['title'], article['seo_focus']):
            added_count += 1
    
    print(f"✅ Загружено {added_count} новых статей в базу данных")
    
    # Показываем статистику
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM plans WHERE status='pending'")
    pending_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM plans WHERE status='published'")
    published_count = cur.fetchone()[0]
    conn.close()
    
    print(f"📊 Статистика базы данных:")
    print(f"   Ожидают публикации: {pending_count}")
    print(f"   Уже опубликованы: {published_count}")

def show_plan_status():
    """Показать текущий статус плана"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    print("\n📋 Текущий статус плана:")
    
    # Показываем ожидающие публикации
    cur.execute("SELECT id, seed, created_at FROM plans WHERE status='pending' ORDER BY created_at")
    pending = cur.fetchall()
    
    if pending:
        print(f"\n⏳ Ожидают публикации ({len(pending)} статей):")
        for i, (plan_id, title, created_at) in enumerate(pending, 1):
            print(f"   {i}. [{plan_id}] {title[:60]}...")
    else:
        print("\n✅ Нет статей, ожидающих публикации")
    
    # Показываем опубликованные
    cur.execute("SELECT id, seed, last_published_at FROM plans WHERE status='published' ORDER BY last_published_at DESC LIMIT 5")
    published = cur.fetchall()
    
    if published:
        print(f"\n✅ Последние опубликованные ({len(published)} статей):")
        for i, (plan_id, title, published_at) in enumerate(published, 1):
            print(f"   {i}. [{plan_id}] {title[:60]}...")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--status':
        show_plan_status()
    else:
        load_plan_to_db()
        show_plan_status()
