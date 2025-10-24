"""wordpress_client.py

Simple helpers to upload media and create posts via WordPress REST API using Application Passwords.
"""
import os
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin
from dotenv import load_dotenv
load_dotenv()

WP_BASE = os.getenv('WP_BASE_URL', '').rstrip('/')
WP_USER = os.getenv('WP_USERNAME')
WP_PASS = os.getenv('WP_APP_PASSWORD')
DISABLE_PUBLISH = os.getenv('DISABLE_WP_PUBLISH', 'false').lower() == 'true'

if not WP_BASE or not WP_USER or not WP_PASS:
    print('[wordpress_client] Warning: WP credentials not configured. Configure .env before using.')

if DISABLE_PUBLISH:
    print('[wordpress_client] ⚠️  WordPress publishing is DISABLED for testing')

def get_or_create_tag(tag_name: str):
    """Get existing tag or create new one, returns tag ID"""
    if not WP_BASE:
        raise RuntimeError('WP_BASE_URL is not set in environment')

    # Clean Application Password
    app_password_clean = WP_PASS.replace(' ', '') if WP_PASS else ''
    auth_clean = HTTPBasicAuth(WP_USER, app_password_clean)

    # Search for existing tag
    search_url = urljoin(WP_BASE, '/wp-json/wp/v2/tags')
    params = {'search': tag_name}

    try:
        resp = requests.get(search_url, auth=auth_clean, params=params)
        resp.raise_for_status()
        tags = resp.json()

        # Check if exact match exists
        for tag in tags:
            if tag.get('name', '').lower() == tag_name.lower():
                print(f"[WordPress] Found existing tag: {tag_name} (ID: {tag.get('id')})")
                return tag.get('id')

        # Tag not found, create new one
        create_data = {'name': tag_name}
        resp = requests.post(search_url, auth=auth_clean, json=create_data)
        resp.raise_for_status()
        new_tag = resp.json()

        print(f"[WordPress] Created new tag: {tag_name} (ID: {new_tag.get('id')})")
        return new_tag.get('id')

    except Exception as e:
        print(f"[WordPress] Error with tag '{tag_name}': {e}")
        return None

def get_or_create_category(category_name: str):
    """Get existing category or create new one, returns category ID"""
    if not WP_BASE:
        raise RuntimeError('WP_BASE_URL is not set in environment')

    # Clean Application Password
    app_password_clean = WP_PASS.replace(' ', '') if WP_PASS else ''
    auth_clean = HTTPBasicAuth(WP_USER, app_password_clean)

    # Search for existing category
    search_url = urljoin(WP_BASE, '/wp-json/wp/v2/categories')
    params = {'search': category_name}

    try:
        resp = requests.get(search_url, auth=auth_clean, params=params)
        resp.raise_for_status()
        categories = resp.json()

        # Check if exact match exists
        for category in categories:
            if category.get('name', '').lower() == category_name.lower():
                print(f"[WordPress] Found existing category: {category_name} (ID: {category.get('id')})")
                return category.get('id')

        # Category not found, create new one
        create_data = {'name': category_name}
        resp = requests.post(search_url, auth=auth_clean, json=create_data)
        resp.raise_for_status()
        new_category = resp.json()

        print(f"[WordPress] Created new category: {category_name} (ID: {new_category.get('id')})")
        return new_category.get('id')

    except Exception as e:
        print(f"[WordPress] Error with category '{category_name}': {e}")
        return None

def upload_image_to_wp(image_bytes: bytes, filename: str, mime_type='image/png'):
    """Uploads an image and returns the JSON response from WP (contains id and source_url)."""
    if not WP_BASE:
        raise RuntimeError('WP_BASE_URL is not set in environment')

    url = urljoin(WP_BASE, '/wp-json/wp/v2/media')
    headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
    files = {'file': (filename, image_bytes, mime_type)}

    # Clean Application Password (remove spaces if any)
    app_password_clean = WP_PASS.replace(' ', '') if WP_PASS else ''
    auth_clean = HTTPBasicAuth(WP_USER, app_password_clean)

    resp = requests.post(url, auth=auth_clean, files=files, headers=headers)
    resp.raise_for_status()
    return resp.json()

def create_wp_post(title, content_html, slug=None, status='publish', featured_media_id=None, meta_description=None, tags=None, categories=None):
    if DISABLE_PUBLISH:
        print(f"[WordPress] 🚫 PUBLISHING DISABLED - Would publish: {title}")
        # Возвращаем фиктивный ответ для тестирования
        return {
            'id': 99999,
            'link': f'https://example.com/test-post-{slug or "test"}',
            'title': title,
            'status': 'draft'  # В тестовом режиме всегда draft
        }
    
    if not WP_BASE:
        raise RuntimeError('WP_BASE_URL is not set in environment')

    url = urljoin(WP_BASE, '/wp-json/wp/v2/posts')

    # Build post data
    data = {
        'title': title,
        'content': content_html,
        'status': status
    }

    if slug:
        data['slug'] = slug
    if featured_media_id:
        data['featured_media'] = featured_media_id
    if meta_description:
        data['excerpt'] = meta_description
    if tags:
        data['tags'] = tags
    if categories:
        data['categories'] = categories

    # Clean Application Password (remove spaces if any)
    app_password_clean = WP_PASS.replace(' ', '') if WP_PASS else ''
    auth_clean = HTTPBasicAuth(WP_USER, app_password_clean)

    print(f"[WordPress] Creating post: {title}")
    print(f"[WordPress] URL: {url}")
    print(f"[WordPress] User: {WP_USER}")

    resp = requests.post(url, auth=auth_clean, json=data)

    if resp.status_code != 201:
        print(f"[WordPress] Error {resp.status_code}: {resp.text}")
        resp.raise_for_status()

    result = resp.json()
    print(f"[WordPress] Post created successfully: ID={result.get('id')}, Link={result.get('link')}")
    return result
