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
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gemini_client import generate_article_with_image
from wordpress_client import upload_image_to_wp, create_wp_post, get_or_create_tag, get_or_create_category
from social_content_generator import SocialContentGenerator
from social_media_clients import SocialMediaCoordinator

load_dotenv()

# Настройка логирования
# Используем только FileHandler чтобы избежать дублирования при запуске через nohup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Очищаем существующие handlers чтобы избежать дублирования при повторном импорте
if logger.handlers:
    logger.handlers.clear()

# Добавляем только FileHandler
file_handler = logging.FileHandler('auto_publisher.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Предотвращаем propagation к root logger
logger.propagate = False

DB_FILE = 'storage.db'
PUBLISH_INTERVAL_DAYS = 3
RETRY_DELAY_MINUTES = 60  # При ошибке генерации ждем 1 час перед повторной попыткой

# Глобальная переменная для отслеживания последней неудачной попытки
last_failed_attempt = None

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
    cur.execute("SELECT id, seed, seo_focus, created_at, last_published_at, category FROM plans WHERE status='pending' ORDER BY created_at LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row

def mark_plan_published(plan_id):
    """Отметить план как опубликованный"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('UPDATE plans SET last_published_at=?, status=? WHERE id=?', 
                (datetime.now(timezone.utc).isoformat(), 'published', plan_id))
    conn.commit()
    conn.close()

def save_post_record(title, slug, wp_id, keywords):
    """Сохранить запись о опубликованном посте"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('INSERT INTO posts (title, slug, wp_id, published_at, seo_keywords) VALUES (?, ?, ?, ?, ?)',
                (title, slug, wp_id, datetime.now(timezone.utc).isoformat(), str(keywords)))
    conn.commit()
    conn.close()

def publish_next_article():
    """Опубликовать следующую статью"""
    logger.info("🔍 [DEBUG] publish_next_article() вызвана")
    logger.info(f"🔍 [DEBUG] Текущее время: {datetime.now(timezone.utc).isoformat()}")

    try:
        logger.info("🔍 [DEBUG] Получаем следующий план...")
        plan = get_next_plan()
        logger.info(f"🔍 [DEBUG] План получен: {plan is not None}")

        if not plan:
            logger.info("Нет статей, ожидающих публикации")
            return False

        plan_id, seed, seo_focus, created_at, last_pub, category = plan
        logger.info(f"🔍 [DEBUG] План ID: {plan_id}, Категория: {category}")
        logger.info(f"Публикуем статью: {seed[:50]}... (категория: {category})")

        # Генерируем статью и изображение
        logger.info("🔍 [DEBUG] Генерируем статью...")
        article = generate_article_with_image(topic=seed)

        # CRITICAL: Validate article was generated successfully
        if not article:
            logger.error(f"❌ FAILED: Article generation failed for topic: {seed}")
            logger.error("❌ Article will NOT be published. Skipping to prevent bad content.")
            logger.info("💡 TIP: Will retry this article on next run")
            return False

        # Extract and validate all required fields
        title = article.get('title')
        slug = article.get('slug')
        meta = article.get('meta_description')
        keywords = article.get('keywords') or []
        content_html = article.get('content')
        image_prompt = article.get('image_prompt', f'Illustration for: {seed}')

        # Double-check critical fields
        if not title or not slug or not content_html:
            logger.error(f"❌ FAILED: Missing critical fields in article")
            logger.error(f"   Title: {bool(title)}, Slug: {bool(slug)}, Content: {bool(content_html)}")
            logger.error("❌ Article will NOT be published. Skipping to prevent incomplete content.")
            return False
        
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
        
        # Получаем ID категории
        category_ids = []
        if category:
            try:
                category_id = get_or_create_category(category)
                if category_id:
                    category_ids.append(category_id)
                    logger.info(f"Категория установлена: {category} (ID: {category_id})")
            except Exception as e:
                logger.warning(f"Ошибка создания категории {category}: {e}")
        
        # Публикуем статью
        wp_post = create_wp_post(
            title=title,
            content_html=content_html,
            slug=slug,
            status='publish',
            featured_media_id=featured_media_id,
            meta_description=meta,
            tags=tag_ids if tag_ids else None,
            categories=category_ids if category_ids else None
        )
        
        wp_id = wp_post.get('id')
        wp_url = wp_post.get('link', f"{os.getenv('WP_BASE_URL')}/{slug}")

        logger.info(f"✅ Статья опубликована в WordPress: {title} -> WP ID: {wp_id}")
        logger.info(f"📎 URL: {wp_url}")

        # Публикация в социальные сети
        enable_social_media = os.getenv('ENABLE_SOCIAL_MEDIA', 'true').lower() == 'true'

        if enable_social_media:
            logger.info("📱 Начинаем публикацию в социальные сети...")
            try:
                # Генерируем контент для социальных сетей
                social_generator = SocialContentGenerator()
                social_posts = social_generator.generate_social_posts(
                    article_title=title,
                    article_url=wp_url,
                    article_content=content_html[:1000],  # Первые 1000 символов для контекста
                    keywords=keywords
                )

                # Публикуем во все настроенные социальные сети
                social_coordinator = SocialMediaCoordinator()
                social_results = social_coordinator.publish_to_all(
                    posts_data=social_posts,
                    image_path=article.get("image_url")  # Передаем путь к изображению
                )

                # Подсчитываем успешные публикации
                successful_posts = sum(1 for r in social_results.values() if r.get('success'))
                total_platforms = len(social_results)

                logger.info(f"📱 Социальные сети: {successful_posts}/{total_platforms} публикаций успешны")

                # Логируем детали
                for platform, result in social_results.items():
                    if result.get('success'):
                        logger.info(f"   ✅ {platform}: {result.get('post_id')}")
                    else:
                        logger.warning(f"   ⚠️  {platform}: {result.get('reason', 'failed')}")

            except Exception as e:
                logger.error(f"❌ Ошибка публикации в социальные сети: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Продолжаем работу даже если публикация в соцсети не удалась
        else:
            logger.info("📱 Публикация в социальные сети отключена (ENABLE_SOCIAL_MEDIA=false)")

        # Сохраняем запись о публикации
        save_post_record(title, slug, wp_id, keywords)
        mark_plan_published(plan_id)

        logger.info(f"✅ Публикация завершена: {title}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка публикации статьи: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def get_status():
    """Получить статус системы"""
    logger.info("🔍 [DEBUG] get_status() вызвана")
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM plans WHERE status='pending'")
    pending_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM plans WHERE status='published'")
    published_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM posts")
    total_posts = cur.fetchone()[0]
    
    # Получаем время последней публикации из таблицы posts
    cur.execute("SELECT published_at FROM posts ORDER BY published_at DESC LIMIT 1")
    last_publish_row = cur.fetchone()
    
    conn.close()
    
    logger.info(f"🔍 [DEBUG] Статистика БД: pending={pending_count}, published={published_count}, posts={total_posts}")
    logger.info(f"🔍 [DEBUG] Последняя публикация в posts: {last_publish_row}")
    
    last_publish_time = None
    next_publish = datetime.now(timezone.utc) + timedelta(days=PUBLISH_INTERVAL_DAYS)
    
    if last_publish_row and last_publish_row[0]:
        try:
            last_publish_time = datetime.fromisoformat(last_publish_row[0])
            # Если дата без timezone, добавляем UTC
            if last_publish_time.tzinfo is None:
                last_publish_time = last_publish_time.replace(tzinfo=timezone.utc)
            next_publish = last_publish_time + timedelta(days=PUBLISH_INTERVAL_DAYS)
            logger.info(f"🔍 [DEBUG] Последняя публикация: {last_publish_time}")
            logger.info(f"🔍 [DEBUG] Следующая публикация: {next_publish}")
        except ValueError as e:
            logger.error(f"🔍 [DEBUG] Ошибка парсинга времени: {e}")
            pass
    
    result = {
        'pending_articles': pending_count,
        'published_articles': published_count,
        'total_posts': total_posts,
        'last_publish_time': last_publish_time,
        'next_publish': next_publish
    }
    
    logger.info(f"🔍 [DEBUG] get_status() возвращает: {result}")
    return result

def run_scheduler():
    """Запуск планировщика"""
    global last_failed_attempt

    logger.info("🚀 Запуск автоматического публикатора статей")
    logger.info(f"📅 Интервал публикации: каждые {PUBLISH_INTERVAL_DAYS} дней")
    logger.info(f"⏱️  Задержка при ошибке: {RETRY_DELAY_MINUTES} минут")

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
            current_time = datetime.now(timezone.utc)

            # Получаем актуальный статус
            status = get_status()

            # Проверяем, нужно ли публиковать статью
            should_publish = False

            logger.info(f"🔍 [DEBUG] Проверка времени публикации:")
            logger.info(f"🔍 [DEBUG] - Текущее время: {current_time}")
            logger.info(f"🔍 [DEBUG] - Последняя публикация: {status['last_publish_time']}")
            logger.info(f"🔍 [DEBUG] - Следующая публикация: {status['next_publish']}")

            # ВАЖНО: Проверяем задержку после неудачной попытки
            if last_failed_attempt:
                time_since_failure = current_time - last_failed_attempt
                minutes_since_failure = time_since_failure.total_seconds() / 60
                logger.info(f"🔍 [DEBUG] - Последняя неудачная попытка: {last_failed_attempt}")
                logger.info(f"🔍 [DEBUG] - Прошло минут с ошибки: {minutes_since_failure:.1f}")

                if minutes_since_failure < RETRY_DELAY_MINUTES:
                    remaining = RETRY_DELAY_MINUTES - minutes_since_failure
                    logger.info(f"⏸️  Ожидание после ошибки: еще {remaining:.0f} минут до повторной попытки")
                    # Пропускаем публикацию, даже если время наступило
                    should_publish = False
                else:
                    logger.info(f"✅ Задержка после ошибки прошла, можно попробовать снова")
                    last_failed_attempt = None  # Сбрасываем после окончания задержки

            # Проверяем время публикации только если нет активной задержки
            if not should_publish and not last_failed_attempt:
                if status['last_publish_time'] is None:
                    # Первая публикация - публикуем сразу
                    should_publish = True
                    logger.info("🎯 Первая публикация - публикуем статью")
                else:
                    # Проверяем интервал с последней публикации
                    time_since_last = current_time - status['last_publish_time']
                    logger.info(f"🔍 [DEBUG] - Время с последней публикации: {time_since_last}")
                    logger.info(f"🔍 [DEBUG] - Требуемый интервал: {timedelta(days=PUBLISH_INTERVAL_DAYS)}")

                    if time_since_last >= timedelta(days=PUBLISH_INTERVAL_DAYS):
                        should_publish = True
                        logger.info(f"⏰ Прошло {time_since_last.days} дней {time_since_last.seconds//3600} часов с последней публикации - время публиковать")
                    else:
                        time_until_next = status['next_publish'] - current_time
                        days_remaining = time_until_next.days
                        hours_remaining = time_until_next.seconds // 3600
                        logger.info(f"⏳ До следующей публикации: {days_remaining} дней {hours_remaining} часов")

            logger.info(f"🔍 [DEBUG] Решение о публикации: {should_publish}")

            if should_publish:
                logger.info("🔍 [DEBUG] Запускаем публикацию статьи...")
                success = publish_next_article()
                logger.info(f"🔍 [DEBUG] Результат публикации: {success}")
                if success:
                    # Обновляем статус после публикации
                    status = get_status()
                    logger.info(f"📊 Обновленный статус: {status['pending_articles']} статей ожидают публикации")
                    logger.info(f"📅 Следующая публикация: {status['next_publish'].strftime('%Y-%m-%d %H:%M')}")
                    # Сбрасываем счетчик ошибок при успешной публикации
                    last_failed_attempt = None
                else:
                    # Запоминаем время неудачной попытки
                    last_failed_attempt = current_time
                    logger.error(f"❌ Не удалось опубликовать статью")
                    logger.info(f"⏸️  Следующая попытка будет через {RETRY_DELAY_MINUTES} минут")
            
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
