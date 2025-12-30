"""main.py

FastAPI app that schedules periodic article generation & publishing.
Endpoints:
- POST /plan {seed, seo_focus}
- POST /publish-now
- GET /status
"""
import os
import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from gemini_client import generate_article_with_image
from wordpress_client import create_wp_post

load_dotenv()
from gemini_client import GeminiClient
from wordpress_client import upload_image_to_wp, create_wp_post, get_or_create_tag

# PUBLISH_INTERVAL_DAYS = int(os.getenv('PUBLISH_INTERVAL_DAYS', '3'))
DB_FILE = 'storage.db'

def init_db():
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

init_db()
gemini = GeminiClient()
app = FastAPI(title='AutoPoster')

class PlanIn(BaseModel):
    seed: str
    seo_focus: str = ''

@app.post('/plan')
def add_plan(plan: PlanIn):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('INSERT INTO plans (seed, seo_focus, created_at, status) VALUES (?, ?, ?, ?)',
                (plan.seed, plan.seo_focus, datetime.utcnow().isoformat(), 'pending'))
    conn.commit()
    conn.close()
    return {'status':'ok'}

def get_next_plan():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, seed, seo_focus, created_at, last_published_at FROM plans WHERE status='pending' ORDER BY created_at LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row

def mark_plan_published(plan_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('UPDATE plans SET last_published_at=?, status=? WHERE id=?', (datetime.utcnow().isoformat(), 'published', plan_id))
    conn.commit()
    conn.close()

def save_post_record(title, slug, wp_id, keywords):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('INSERT INTO posts (title, slug, wp_id, published_at, seo_keywords) VALUES (?, ?, ?, ?, ?)',
                (title, slug, wp_id, datetime.utcnow().isoformat(), json.dumps(keywords)))
    conn.commit()
    conn.close()

def publish_next():
    plan = get_next_plan()
    if not plan:
        print('No pending plans.')
        return
    plan_id, seed, seo_focus, created_at, last_pub = plan
    print('Publishing plan:', plan_id, seed)
    result = gemini.generate_article(brief_plan=seed, seo_focus=seo_focus, word_count=900)
    title = result.get('title') or 'Auto article'
    slug = result.get('slug')
    meta = result.get('meta_description')
    keywords = result.get('keywords') or []
    content_html = result.get('content_html') or result.get('content') or ''
    image_prompt = result.get('image_prompt') or f'Illustration for: {seed}'
    # Generate image
    try:
        image_bytes, mime = gemini.generate_image(image_prompt)
    except Exception as e:
        print('Image gen failed:', e)
        image_bytes, mime = None, None
    featured_media_id = None
    if image_bytes:
        upload = upload_image_to_wp(image_bytes, filename=f"{(slug or 'img')}_{int(datetime.utcnow().timestamp())}.png", mime_type=mime)
        featured_media_id = upload.get('id')
    wp_post = create_wp_post(title=title, content_html=content_html, slug=slug, status='publish', featured_media_id=featured_media_id, meta_description=meta)
    wp_id = wp_post.get('id')
    save_post_record(title, slug, wp_id, keywords)
    mark_plan_published(plan_id)
    print('Published', title, '->', wp_id)

# scheduler = BackgroundScheduler()
# scheduler.add_job(publish_next, 'interval', days=PUBLISH_INTERVAL_DAYS, next_run_time=datetime.utcnow())
# scheduler.start()
# 
# ВНИМАНИЕ: Планировщик отключен для избежания конфликтов с thenextai_publisher.py
# Используйте только thenextai_publisher.py для автоматической публикации

@app.get('/status')
def status():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM posts')
    posts = cur.fetchone()[0]
    cur.execute('SELECT id, seed, status FROM plans')
    plans = cur.fetchall()
    conn.close()
    return {'published_posts': posts, 'plans': plans}

@app.post('/publish-now')
def publish_now(background: BackgroundTasks):
    background.add_task(publish_next)
    return {'status':'publishing started'}

class GenerateRequest(BaseModel):
    topic: str
    seo_focus: str = ""
    status: str = "publish"  # 'publish' or 'draft'

@app.post("/generate")
async def generate(request: GenerateRequest = None):
    try:
        # Default topic if none provided
        if request is None:
            topic = "AI Technology Insights"
            seo_focus = ""
        else:
            topic = request.topic
            seo_focus = request.seo_focus if request.seo_focus else request.topic

        print(f"[Main] Generating article on topic: {topic}")

        # 1️⃣ Генерируем статью и изображение
        article = generate_article_with_image(topic=topic)

        # 2️⃣ Загружаем изображение на WordPress
        featured_media_id = None
        if article.get("image_url"):
            # Читаем локальное изображение
            with open(article["image_url"], "rb") as f:
                image_bytes = f.read()

            # Загружаем на WordPress
            import os
            filename = os.path.basename(article["image_url"])
            upload_result = upload_image_to_wp(image_bytes, filename, mime_type='image/png')
            featured_media_id = upload_result.get('id')
            print(f"[Main] Image uploaded: {featured_media_id}")

        # 3️⃣ Создаем или находим теги
        tag_ids = []
        if article.get("keywords"):
            print(f"[Main] Processing {len(article['keywords'])} keywords as tags...")
            for keyword in article["keywords"]:
                tag_id = get_or_create_tag(keyword)
                if tag_id:
                    tag_ids.append(tag_id)
            print(f"[Main] Tag IDs: {tag_ids}")

        # 4️⃣ Публикуем статью на сайт
        post_status = request.status if request else "publish"
        result = create_wp_post(
            title=article["title"],
            content_html=article["content"],
            featured_media_id=featured_media_id,
            tags=tag_ids if tag_ids else None,
            status=post_status
        )

        return JSONResponse(content={
            "message": "Article published successfully!",
            "post_id": result.get('id'),
            "title": article["title"],
            "link": result.get('link'),
            "featured_image": featured_media_id,
            "tags": tag_ids,
            "status": post_status
        })

    except Exception as e:
        import traceback
        print(f"[Main] Error: {e}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()}
        )