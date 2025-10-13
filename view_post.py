"""View a WordPress post details"""
import sys
import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv
import html

load_dotenv()

WP_BASE = os.getenv('WP_BASE_URL', '').rstrip('/')
WP_USER = os.getenv('WP_USERNAME')
WP_PASS = os.getenv('WP_APP_PASSWORD', '').replace(' ', '')

if len(sys.argv) < 2:
    print("Usage: python view_post.py <post_id>")
    sys.exit(1)

post_id = sys.argv[1]

print("=" * 80)
print(f"Fetching post ID: {post_id}")
print("=" * 80)
print()

# Fetch post
url = f"{WP_BASE}/wp-json/wp/v2/posts/{post_id}"
resp = requests.get(url, auth=HTTPBasicAuth(WP_USER, WP_PASS))

if resp.status_code != 200:
    print(f"Error: {resp.status_code}")
    print(resp.text)
    sys.exit(1)

post = resp.json()

# Display post info
print(f"Title: {post.get('title', {}).get('rendered')}")
print(f"Slug: {post.get('slug')}")
print(f"Status: {post.get('status')}")
print(f"Link: {post.get('link')}")
print(f"Date: {post.get('date')}")
print(f"Modified: {post.get('modified')}")
print()

# Display excerpt
if post.get('excerpt', {}).get('rendered'):
    print("Excerpt:")
    print("-" * 80)
    print(html.unescape(post.get('excerpt', {}).get('rendered')))
    print("-" * 80)
    print()

# Display content (first 1000 chars)
content_html = post.get('content', {}).get('rendered', '')
if content_html:
    print("Content (first 1000 characters):")
    print("-" * 80)
    # Remove HTML tags for preview
    import re
    content_text = re.sub('<[^<]+?>', '', content_html)
    content_text = html.unescape(content_text)
    print(content_text[:1000])
    if len(content_text) > 1000:
        print("\n... (truncated)")
    print("-" * 80)
    print()
    print(f"Total content length: {len(content_text)} characters")

# Featured image
if post.get('featured_media'):
    print(f"\nFeatured media ID: {post.get('featured_media')}")

# Categories and tags
if post.get('categories'):
    print(f"Categories: {post.get('categories')}")
if post.get('tags'):
    print(f"Tags: {post.get('tags')}")

print()
print("=" * 80)
print(f"View full post at: {post.get('link')}")
print("=" * 80)
