# Automatic Article Publisher

Automated system for generating and publishing articles to WordPress every 3 days.

## 🚀 Quick Start

### 1. Load Article Plan
```bash
# Load articles from plan.txt into database
python load_plan.py

# Show plan status
python load_plan.py --status
```

### 2. Start Automatic Publisher
```bash
# Start in background mode
./start_auto_publisher.sh

# Check status
./monitor_auto_publisher.sh

# Stop
./stop_auto_publisher.sh
```

## 📋 Management

### Plan Management Commands
```bash
# Load article plan
python load_plan.py

# Show plan status
python load_plan.py --status
```

### Publisher Commands
```bash
# Show system status
python auto_publisher.py --status

# Publish article now
python auto_publisher.py --publish-now

# Run in daemon mode (manually)
python auto_publisher.py
```

### Management Scripts
```bash
# Start in background mode
./start_auto_publisher.sh

# Monitor
./monitor_auto_publisher.sh

# Stop
./stop_auto_publisher.sh
```

## 📊 Monitoring

### View Logs
```bash
# View logs in real-time
tail -f logs/auto_publisher.out

# Last 50 lines
tail -50 logs/auto_publisher.out
```

### Check Status
```bash
# Full status
./monitor_auto_publisher.sh

# Database status only
python auto_publisher.py --status
```

## 🗄️ Database

The system uses SQLite database `storage.db` with the following tables:

### `plans` Table
- `id` - unique identifier
- `seed` - article title
- `seo_focus` - SEO focus
- `created_at` - creation date
- `last_published_at` - publication date
- `status` - status ('pending' or 'published')

### `posts` Table
- `id` - unique identifier
- `title` - post title
- `slug` - URL slug
- `wp_id` - WordPress ID
- `published_at` - publication date
- `seo_keywords` - keywords

## ⚙️ Settings

### Publication Interval
By default, articles are published every 3 days. To change this, edit the `PUBLISH_INTERVAL_DAYS` variable in `auto_publisher.py`.

### Scheduler Logic
- **On first run**: If there are no published articles in the database, the system will immediately publish the first article
- **On subsequent runs**: The system checks the time of the last publication from the database and publishes the next article only if 3 days have passed
- **Check every 5 minutes**: The system checks if it's time to publish an article
- **Status every 6 hours**: Current system status is displayed in logs

### Logging
Logs are saved to `auto_publisher.log` file and displayed in console.

## 🔧 Troubleshooting

### Publisher Won't Start
```bash
# Check if already running
ps aux | grep auto_publisher

# Stop all processes
pkill -f auto_publisher.py

# Restart
./start_auto_publisher.sh
```

### Errors in Logs
```bash
# View errors
grep -i error logs/auto_publisher.out

# View recent errors
tail -100 logs/auto_publisher.out | grep -i error
```

### Database Issues
```bash
# Check database
sqlite3 storage.db ".tables"
sqlite3 storage.db "SELECT COUNT(*) FROM plans WHERE status='pending';"
```

## 📁 File Structure

```
wordpress-auto-poster/
├── auto_publisher.py          # Main publisher script
├── load_plan.py              # Article plan loader
├── start_auto_publisher.sh   # Start script
├── stop_auto_publisher.sh    # Stop script
├── monitor_auto_publisher.sh # Monitor script
├── plan.txt                  # Article plan
├── storage.db                # SQLite database
├── logs/                     # Logs directory
│   ├── auto_publisher.out    # Publisher logs
│   └── auto_publisher.pid    # PID file
└── generated_images/         # Generated images
```

## 🎯 Usage Examples

### Adding New Articles to Plan
1. Edit the `plan.txt` file
2. Run `python load_plan.py`
3. New articles will be added to the queue

### Manual Article Publication
```bash
python auto_publisher.py --publish-now
```

### System Health Check
```bash
# Full monitoring
./monitor_auto_publisher.sh

# Status only
python auto_publisher.py --status
```

## 🔄 Auto-start on System Boot

To automatically start on system boot, add to crontab:

```bash
# Edit crontab
crontab -e

# Add line for boot startup
@reboot cd /path/to/wordpress-auto-poster && ./start_auto_publisher.sh
```

## 📞 Support

If you encounter issues:
1. Check logs: `tail -f logs/auto_publisher.out`
2. Check status: `./monitor_auto_publisher.sh`
3. Restart system: `./stop_auto_publisher.sh && ./start_auto_publisher.sh`
