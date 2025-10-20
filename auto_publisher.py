#!/usr/bin/env python3
"""
Автоматический публикатор статей
Запускает публикацию статей каждые 3 дня
"""

import os
import sys
import time
import logging
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gemini_client import generate_article_with_image
from wordpress_client import upload_image_to_wp, create_wp_post, get_or_create_tag

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_publisher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB_FILE = 'storage.db'
PUBLISH_INTERVAL_DAYS = 3

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

def get_next_plan():
    """Получить следующую статью для публикации"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, seed, seo_focus, created_at, last_published_at FROM plans WHERE status='pending' ORDER BY created_at LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row

def mark_plan_published(plan_id):
    """Отметить план как опубликованный"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('UPDATE plans SET last_published_at=?, status=? WHERE id=?', 
                (datetime.now().isoformat(), 'published', plan_id))
    conn.commit()
    conn.close()

def save_post_record(title, slug, wp_id, keywords):
    """Сохранить запись о опубликованном посте"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('INSERT INTO posts (title, slug, wp_id, published_at, seo_keywords) VALUES (?, ?, ?, ?, ?)',
                (title, slug, wp_id, datetime.now().isoformat(), str(keywords)))
    conn.commit()
    conn.close()

def publish_next_article():
    """Опубликовать следующую статью"""
    try:
        plan = get_next_plan()
        if not plan:
            logger.info("Нет статей, ожидающих публикации")
            return False
        
        plan_id, seed, seo_focus, created_at, last_pub = plan
        logger.info(f"Публикуем статью: {seed[:50]}...")
        
        # Генерируем статью и изображение
        article = generate_article_with_image(topic=seed)
        
        title = article.get('title') or seed
        slug = article.get('slug')
        meta = article.get('meta_description')
        keywords = article.get('keywords') or []
        content_html = article.get('content')
        image_prompt = article.get('image_prompt', f'Illustration for: {seed}')
        
        # Загружаем изображение на WordPress
        featured_media_id = None
        if article.get("image_url"):
            try:
                with open(article["image_url"], "rb") as f:
                    image_bytes = f.read()
                
                filename = os.path.basename(article["image_url"])
                upload_result = upload_image_to_wp(image_bytes, filename, mime_type='image/png')
                featured_media_id = upload_result.get('id')
                logger.info(f"Изображение загружено: {featured_media_id}")
            except Exception as e:
                logger.error(f"Ошибка загрузки изображения: {e}")
        
        # Создаем теги
        tag_ids = []
        if keywords:
            for keyword in keywords:
                try:
                    tag_id = get_or_create_tag(keyword)
                    if tag_id:
                        tag_ids.append(tag_id)
                except Exception as e:
                    logger.warning(f"Ошибка создания тега {keyword}: {e}")
        
        # Публикуем статью
        wp_post = create_wp_post(
            title=title,
            content_html=content_html,
            slug=slug,
            status='publish',
            featured_media_id=featured_media_id,
            meta_description=meta,
            tags=tag_ids if tag_ids else None
        )
        
        wp_id = wp_post.get('id')
        save_post_record(title, slug, wp_id, keywords)
        mark_plan_published(plan_id)
        
        logger.info(f"✅ Статья опубликована: {title} -> WP ID: {wp_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка публикации статьи: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def get_status():
    """Получить статус системы"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM plans WHERE status='pending'")
    pending_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM plans WHERE status='published'")
    published_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM posts")
    total_posts = cur.fetchone()[0]
    
    # Получаем время последней публикации
    cur.execute("SELECT last_published_at FROM plans WHERE status='published' ORDER BY last_published_at DESC LIMIT 1")
    last_publish_row = cur.fetchone()
    
    conn.close()
    
    last_publish_time = None
    next_publish = datetime.now() + timedelta(days=PUBLISH_INTERVAL_DAYS)
    
    if last_publish_row and last_publish_row[0]:
        try:
            last_publish_time = datetime.fromisoformat(last_publish_row[0])
            next_publish = last_publish_time + timedelta(days=PUBLISH_INTERVAL_DAYS)
        except ValueError:
            pass
    
    return {
        'pending_articles': pending_count,
        'published_articles': published_count,
        'total_posts': total_posts,
        'last_publish_time': last_publish_time,
        'next_publish': next_publish
    }

def run_scheduler():
    """Запуск планировщика"""
    logger.info("🚀 Запуск автоматического публикатора статей")
    logger.info(f"📅 Интервал публикации: каждые {PUBLISH_INTERVAL_DAYS} дней")
    
    # Инициализируем базу данных
    init_db()
    
    # Показываем начальный статус
    status = get_status()
    logger.info(f"📊 Статус: {status['pending_articles']} статей ожидают публикации, {status['published_articles']} уже опубликованы")
    
    if status['last_publish_time']:
        logger.info(f"📅 Последняя публикация: {status['last_publish_time'].strftime('%Y-%m-%d %H:%M')}")
        logger.info(f"📅 Следующая публикация: {status['next_publish'].strftime('%Y-%m-%d %H:%M')}")
    else:
        logger.info("📅 Это первая публикация")
    
    while True:
        try:
            current_time = datetime.now()
            
            # Получаем актуальный статус
            status = get_status()
            
            # Проверяем, нужно ли публиковать статью
            should_publish = False
            
            if status['last_publish_time'] is None:
                # Первая публикация - публикуем сразу
                should_publish = True
                logger.info("🎯 Первая публикация - публикуем статью")
            else:
                # Проверяем интервал с последней публикации
                time_since_last = current_time - status['last_publish_time']
                if time_since_last >= timedelta(days=PUBLISH_INTERVAL_DAYS):
                    should_publish = True
                    logger.info(f"⏰ Прошло {time_since_last.days} дней с последней публикации - время публиковать")
                else:
                    days_remaining = (status['next_publish'] - current_time).days
                    logger.info(f"⏳ До следующей публикации: {days_remaining} дней")
            
            if should_publish:
                success = publish_next_article()
                if success:
                    # Обновляем статус после публикации
                    status = get_status()
                    logger.info(f"📊 Обновленный статус: {status['pending_articles']} статей ожидают публикации")
                    logger.info(f"📅 Следующая публикация: {status['next_publish'].strftime('%Y-%m-%d %H:%M')}")
                else:
                    logger.error("❌ Не удалось опубликовать статью")
            
            # Показываем статус каждые 6 часов
            if current_time.hour % 6 == 0 and current_time.minute < 5:
                status = get_status()
                logger.info(f"📊 Статус: {status['pending_articles']} статей ожидают, следующая публикация: {status['next_publish'].strftime('%Y-%m-%d %H:%M')}")
            
            # Ждем 5 минут перед следующей проверкой
            time.sleep(300)  # 5 минут
            
        except KeyboardInterrupt:
            logger.info("🛑 Получен сигнал остановки")
            break
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
            import traceback
            logger.error(traceback.format_exc())
            time.sleep(60)  # Ждем минуту перед повтором
    
    logger.info("👋 Автоматический публикатор остановлен")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Автоматический публикатор статей')
    parser.add_argument('--status', action='store_true', help='Показать статус')
    parser.add_argument('--publish-now', action='store_true', help='Опубликовать статью сейчас')
    parser.add_argument('--daemon', action='store_true', help='Запустить в режиме демона')
    
    args = parser.parse_args()
    
    if args.status:
        init_db()
        status = get_status()
        print(f"📊 Статус системы:")
        print(f"   Статей ожидают публикации: {status['pending_articles']}")
        print(f"   Статей уже опубликованы: {status['published_articles']}")
        print(f"   Всего постов: {status['total_posts']}")
        print(f"   Следующая публикация: {status['next_publish'].strftime('%Y-%m-%d %H:%M')}")
    elif args.publish_now:
        init_db()
        success = publish_next_article()
        if success:
            print("✅ Статья опубликована успешно")
        else:
            print("❌ Не удалось опубликовать статью")
    else:
        run_scheduler()
