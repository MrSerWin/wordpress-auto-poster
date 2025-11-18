# AutoPoster — WordPress Auto Publisher with Gemini AI Integration

Application for automatic article publishing to WordPress using artificial intelligence (Gemini) for content and image generation.

## Key Features

- Automatic article generation using Gemini AI
- Image generation for articles
- WordPress publishing via REST API
- **NEW: Automatic social media publishing** (Facebook, Twitter/X, Threads, VK, Instagram)
- **NEW: AI-generated social media content** with platform-specific optimization
- **NEW: Smart hashtag generation** for each platform
- Scheduler for periodic publishing
- SEO content optimization
- REST API for publication management
- Rate limiting and retry logic for API calls

## Project Structure

- `main.py` — FastAPI server + publication scheduler
- `gemini_client.py` — client for working with Gemini/Google GenAI
- `wordpress_client.py` — media upload and post creation via WordPress REST API
- `requirements.txt` — project dependencies
- `.env` — environment variables (don't commit!)
- `run.sh` — application startup script

## Quick Start

### 1. Installation and Setup

```bash
# Clone repository and navigate to folder
cd wordpress-auto-poster

# Create .env file with your settings
cat > .env << EOF
GOOGLE_API_KEY=your_google_api_key
WP_BASE_URL=https://your-site.com
WP_USERNAME=your_wp_username
WP_APP_PASSWORD=your_application_password
PUBLISH_INTERVAL_DAYS=3
EOF
```

### 2. WordPress Application Password Setup

**IMPORTANT:** WordPress REST API requires Application Password (not regular admin password!)

1. Go to WordPress Admin: `https://your-site.com/wp-admin`
2. Navigate: **Users → Profile** (or **Users → [your-user]**)
3. Scroll down to **"Application Passwords"** section
4. Enter a name (e.g., "Auto Poster") and click **"Add New Application Password"**
5. **Copy the generated password** (shown only once!)
6. Use this password in `.env` file (with or without spaces)

### 3. Running the Application

```bash
# Simple startup via script
./run.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8011
```

Server will be available at: http://127.0.0.1:8000

API documentation: http://127.0.0.1:8000/docs

## API Endpoints

### `POST /generate`
Generates and publishes an article immediately

```bash
curl -X POST http://127.0.0.1:8000/generate
```

Response:
```json
{
  "message": "Article published successfully!",
  "post_id": 190,
  "link": "https://your-site.com/post-slug/",
  "featured_image": 189
}
```

### `POST /plan`
Adds an article plan for future publication

```bash
curl -X POST http://127.0.0.1:8000/plan \
  -H "Content-Type: application/json" \
  -d '{"seed": "Artificial Intelligence in Medicine", "seo_focus": "AI healthcare"}'
```

### `POST /publish-now`
Starts publishing the next scheduled article

```bash
curl -X POST http://127.0.0.1:8000/publish-now
```

### `GET /status`
Checks application status and number of published articles

```bash
curl http://127.0.0.1:8000/status
```

## Troubleshooting

### 401 Unauthorized Error

If you get authentication error:

1. **Check Application Password** - this is NOT a regular admin password
2. **Create new Application Password** in WordPress (see instructions above)
3. **Update `.env` file** with new password
4. **Restart application** - important that there are no environment variables in shell

```bash
# Clear environment variables and restart
unset WP_APP_PASSWORD WP_USERNAME WP_BASE_URL
./run.sh
```

### Authentication Testing

Use built-in scripts for diagnostics:

```bash
# Full WordPress diagnostics
python diagnose_wp.py

# Authentication test
python test_wp_auth.py

# Interactive password setup
python setup_wp_password.py
```

## Important Notes

- **Application Password ≠ regular password** - create separate password for API
- **Don't commit `.env`** file to git (added to `.gitignore`)
- **Password without quotes** - in `.env` don't use quotes around values
- **HTTPS required** - Application Passwords work only over HTTPS
- **User permissions** - user must have Editor or Administrator role

## Requirements

- Python 3.8+
- macOS (or Linux/Windows with minor changes)
- WordPress 5.6+ with Application Passwords enabled
- HTTPS on WordPress site
- Google Gemini API key

## 📱 Social Media Integration (NEW!)

**Automatically publish articles to 5 social networks after WordPress publication!**

### Features:
- 🤖 AI-generated unique content for each platform
- 📊 Platform-specific optimization (length, style, tone)
- #️⃣ Automatic relevant hashtag generation
- 🔗 Direct links to your articles
- ⚙️ Flexible configuration - enable only needed platforms

### Quick Setup:

1. **Enable social media publishing**:
   ```bash
   # In .env file
   ENABLE_SOCIAL_MEDIA=true
   ```

2. **Configure API keys** for desired platforms (see [SOCIAL_MEDIA_SETUP.md](SOCIAL_MEDIA_SETUP.md))

3. **Test the system**:
   ```bash
   python test_social_media_integration.py
   ```

4. **Publish**:
   ```bash
   python auto_publisher.py --publish-now
   ```

### Supported Platforms:
- 📘 **Facebook** - Professional posts with call-to-action
- 🐦 **Twitter/X** - Concise, impactful tweets
- 🧵 **Threads** - Conversational style posts
- 🔵 **VK** - Russian-language audience focus
- 📸 **Instagram** - Visual-focused captions with images

### Documentation:
- **Quick Start (3 min)**: [SOCIAL_MEDIA_QUICKSTART.md](SOCIAL_MEDIA_QUICKSTART.md)
- **Detailed Setup**: [SOCIAL_MEDIA_SETUP.md](SOCIAL_MEDIA_SETUP.md)
- **Summary**: [SUMMARY_SOCIAL_MEDIA.md](SUMMARY_SOCIAL_MEDIA.md)

---

