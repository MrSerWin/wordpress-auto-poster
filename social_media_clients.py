#!/usr/bin/env python3
"""
Клиенты для публикации в социальные сети
Поддерживает: Facebook, Twitter/X, Threads, VK, Instagram
"""
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()


class SocialMediaPublisher:
    """Базовый класс для публикации в социальные сети"""

    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.enabled = False

    def publish(self, text: str, url: str = None, image_path: str = None):
        """Публикует пост в социальную сеть"""
        raise NotImplementedError("Must be implemented in subclass")

    def is_enabled(self):
        """Проверяет, включена ли публикация для этой платформы"""
        return self.enabled


class FacebookPublisher(SocialMediaPublisher):
    """Публикация в Facebook Page"""

    def __init__(self):
        super().__init__("Facebook")
        self.page_id = os.getenv('FACEBOOK_PAGE_ID')
        self.access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        self.enabled = bool(self.page_id and self.access_token)

        if self.enabled:
            print(f"[{self.platform_name}] Initialized")
        else:
            print(f"[{self.platform_name}] Disabled (missing credentials)")

    def publish(self, text: str, url: str = None, image_path: str = None):
        """Публикует пост на Facebook Page"""
        if not self.enabled:
            print(f"[{self.platform_name}] Skipped (not configured)")
            return None

        try:
            api_url = f"https://graph.facebook.com/v18.0/{self.page_id}/feed"

            # Подготовка данных
            data = {
                'message': text,
                'access_token': self.access_token
            }

            if url:
                data['link'] = url

            # Публикация
            response = requests.post(api_url, data=data, timeout=30)
            response.raise_for_status()

            result = response.json()
            post_id = result.get('id')

            print(f"[{self.platform_name}] ✅ Published: {post_id}")
            return post_id

        except Exception as e:
            print(f"[{self.platform_name}] ❌ Error: {e}")
            return None


class TwitterPublisher(SocialMediaPublisher):
    """Публикация в Twitter/X"""

    def __init__(self):
        super().__init__("Twitter/X")
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_secret = os.getenv('TWITTER_ACCESS_SECRET')
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

        self.enabled = bool(
            self.api_key and self.api_secret and
            self.access_token and self.access_secret and
            self.bearer_token
        )

        if self.enabled:
            print(f"[{self.platform_name}] Initialized")
        else:
            print(f"[{self.platform_name}] Disabled (missing credentials)")

    def publish(self, text: str, url: str = None, image_path: str = None):
        """Публикует твит"""
        if not self.enabled:
            print(f"[{self.platform_name}] Skipped (not configured)")
            return None

        try:
            # Twitter API v2
            # Для полноценной реализации потребуется tweepy или requests-oauthlib
            try:
                import tweepy
            except ImportError:
                print(f"[{self.platform_name}] ⚠️ tweepy not installed. Install: pip install tweepy")
                return None

            # Аутентификация
            client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret
            )

            # Публикация
            response = client.create_tweet(text=text)
            tweet_id = response.data['id']

            print(f"[{self.platform_name}] ✅ Published: {tweet_id}")
            return tweet_id

        except Exception as e:
            print(f"[{self.platform_name}] ❌ Error: {e}")
            return None


class ThreadsPublisher(SocialMediaPublisher):
    """Публикация в Threads (временно отключено - проблемы с библиотекой)"""

    def __init__(self):
        super().__init__("Threads")
        self.username = os.getenv('THREADS_USERNAME') or os.getenv('INSTAGRAM_USERNAME')
        self.password = os.getenv('THREADS_PASSWORD') or os.getenv('INSTAGRAM_PASSWORD')
        # Временно отключено из-за проблем с threads-api
        self.enabled = False
        self.api = None

        if self.username and self.password:
            print(f"[{self.platform_name}] ⚠️ Temporarily disabled (library compatibility issues)")
            print(f"[{self.platform_name}] See THREADS_STATUS.md for details and alternatives")
        else:
            print(f"[{self.platform_name}] Disabled (missing credentials)")

    def authenticate(self):
        """Аутентификация в Threads используя Instagram credentials"""
        if self.api:
            return True

        try:
            # ПРИМЕЧАНИЕ: threads-api имеет проблемы с Pydantic v2
            # Ошибка: NameError: Fields must not use names with leading underscores
            # Временно отключено до обновления библиотеки

            # from threads_api.src.threads_api import ThreadsAPI
            # self.api = ThreadsAPI(username=self.username, password=self.password)

            print(f"[{self.platform_name}] ⚠️ threads-api library has compatibility issues")
            print(f"[{self.platform_name}] Use Instagram posting instead")
            return False

        except Exception as e:
            print(f"[{self.platform_name}] ❌ Authentication failed: {e}")
            self.api = None
            return False

    def publish(self, text: str, url: str = None, image_path: str = None):
        """Публикует пост в Threads"""
        if not self.enabled:
            print(f"[{self.platform_name}] Skipped (temporarily disabled)")
            return None

        try:
            # Аутентификация
            if not self.api:
                if not self.authenticate():
                    return None

            # Форматируем текст с URL
            caption = text
            if url:
                caption += f"\n\n{url}"

            # Публикуем (Threads API может поддерживать текст и изображения)
            if image_path and os.path.exists(image_path):
                # Threads с изображением
                result = self.api.publish(caption=caption, image_path=image_path)
            else:
                # Только текст
                result = self.api.publish(caption=caption)

            # Получаем ID поста из результата
            post_id = None
            if isinstance(result, dict):
                post_id = result.get('id') or result.get('post_id') or result.get('media_id')
            elif hasattr(result, 'id'):
                post_id = result.id

            if post_id:
                print(f"[{self.platform_name}] ✅ Published: {post_id}")
                return str(post_id)
            else:
                print(f"[{self.platform_name}] ⚠️ Published but no post_id returned")
                return "published_no_id"

        except Exception as e:
            print(f"[{self.platform_name}] ❌ Error: {e}")
            return None


class VKPublisher(SocialMediaPublisher):
    """Публикация в VK (ВКонтакте)"""

    def __init__(self):
        super().__init__("VK")
        self.access_token = os.getenv('VK_ACCESS_TOKEN')
        self.group_id = os.getenv('VK_GROUP_ID')  # ID группы (без минуса)
        self.enabled = bool(self.access_token and self.group_id)

        if self.enabled:
            print(f"[{self.platform_name}] Initialized")
        else:
            print(f"[{self.platform_name}] Disabled (missing credentials)")

    def publish(self, text: str, url: str = None, image_path: str = None):
        """Публикует пост на стену VK группы с изображением"""
        if not self.enabled:
            print(f"[{self.platform_name}] Skipped (not configured)")
            return None

        try:
            # Подготовка сообщения
            message = text
            if url:
                message += f"\n\n{url}"

            # Параметры для wall.post
            params = {
                'owner_id': f"-{self.group_id}",  # Для группы с минусом
                'from_group': 1,  # От имени группы
                'message': message,
                'access_token': self.access_token,
                'v': '5.131'  # Версия API
            }

            # Загрузка изображения если есть
            if image_path and os.path.exists(image_path):
                try:
                    # Шаг 1: Получить upload URL
                    upload_url_api = "https://api.vk.com/method/photos.getWallUploadServer"
                    upload_params = {
                        'group_id': self.group_id,
                        'access_token': self.access_token,
                        'v': '5.131'
                    }

                    response = requests.get(upload_url_api, params=upload_params, timeout=30)
                    upload_url_data = response.json()

                    if 'error' in upload_url_data:
                        print(f"[{self.platform_name}] ⚠️ Can't get upload URL: {upload_url_data['error']}")
                    else:
                        upload_url = upload_url_data['response']['upload_url']

                        # Шаг 2: Загрузить фото на сервер VK
                        with open(image_path, 'rb') as photo:
                            files = {'photo': photo}
                            upload_response = requests.post(upload_url, files=files, timeout=30)
                            upload_result = upload_response.json()

                        # Шаг 3: Сохранить фото
                        save_url = "https://api.vk.com/method/photos.saveWallPhoto"
                        save_params = {
                            'group_id': self.group_id,
                            'photo': upload_result['photo'],
                            'server': upload_result['server'],
                            'hash': upload_result['hash'],
                            'access_token': self.access_token,
                            'v': '5.131'
                        }

                        save_response = requests.post(save_url, data=save_params, timeout=30)
                        save_result = save_response.json()

                        if 'response' in save_result and len(save_result['response']) > 0:
                            photo_data = save_result['response'][0]
                            photo_id = f"photo{photo_data['owner_id']}_{photo_data['id']}"
                            params['attachments'] = photo_id
                            print(f"[{self.platform_name}] ✅ Image uploaded: {photo_id}")

                except Exception as img_error:
                    print(f"[{self.platform_name}] ⚠️ Image upload failed: {img_error}")
                    # Продолжаем публикацию без изображения

            # Публикация поста
            api_url = "https://api.vk.com/method/wall.post"
            response = requests.post(api_url, data=params, timeout=30)
            response.raise_for_status()

            result = response.json()

            if 'error' in result:
                raise Exception(f"VK API Error: {result['error']}")

            post_id = result.get('response', {}).get('post_id')

            print(f"[{self.platform_name}] ✅ Published: {post_id}")
            return post_id

        except Exception as e:
            print(f"[{self.platform_name}] ❌ Error: {e}")
            return None


class InstagramPublisher(SocialMediaPublisher):
    """Публикация в Instagram (через instagrapi - session-based)"""

    def __init__(self):
        super().__init__("Instagram")
        self.username = os.getenv('INSTAGRAM_USERNAME')
        self.password = os.getenv('INSTAGRAM_PASSWORD')
        self.session_file = os.getenv('INSTAGRAM_SESSION_FILE', '.instagram_session.json')
        self.enabled = bool(self.username and self.password)
        self.client = None

        if self.enabled:
            print(f"[{self.platform_name}] Initialized (session-based)")
        else:
            print(f"[{self.platform_name}] Disabled (missing credentials)")

    def authenticate(self):
        """Аутентификация с сохранением сессии"""
        if self.client:
            return True

        try:
            from instagrapi import Client
            from pathlib import Path

            self.client = Client()

            # Попытка загрузить существующую сессию
            session_path = Path(self.session_file)
            if session_path.exists():
                try:
                    print(f"[{self.platform_name}] Loading saved session...")
                    self.client.load_settings(session_path)
                    self.client.login(self.username, self.password)

                    # Проверяем, что сессия рабочая
                    self.client.get_timeline_feed()
                    print(f"[{self.platform_name}] ✅ Session restored successfully")
                    return True
                except Exception as e:
                    print(f"[{self.platform_name}] ⚠️ Saved session invalid: {e}")
                    print(f"[{self.platform_name}] Performing new login...")

            # Новый логин
            self.client.login(self.username, self.password)

            # Сохраняем сессию
            self.client.dump_settings(session_path)
            print(f"[{self.platform_name}] ✅ Login successful. Session saved to {self.session_file}")
            return True

        except Exception as e:
            print(f"[{self.platform_name}] ❌ Authentication failed: {e}")
            self.client = None
            return False

    def publish(self, text: str, url: str = None, image_path: str = None):
        """
        Публикует пост в Instagram с изображением
        ВАЖНО: Instagram требует изображение для публикации
        """
        if not self.enabled:
            print(f"[{self.platform_name}] Skipped (not configured)")
            return None

        if not image_path or not os.path.exists(image_path):
            print(f"[{self.platform_name}] ⚠️ Warning: Instagram requires an image file. Skipping.")
            return None

        try:
            # Аутентификация
            if not self.client:
                if not self.authenticate():
                    return None

            # Формируем caption с хэштегами
            caption = text
            if url:
                caption += f"\n\n🔗 {url}"

            # Загружаем фото в Instagram
            from pathlib import Path
            media = self.client.photo_upload(
                Path(image_path),
                caption=caption
            )

            media_id = media.pk
            print(f"[{self.platform_name}] ✅ Published: {media_id}")
            return str(media_id)

        except Exception as e:
            print(f"[{self.platform_name}] ❌ Error: {e}")
            return None


class TelegramPublisher(SocialMediaPublisher):
    """Публикация в Telegram канал"""

    def __init__(self):
        super().__init__("Telegram")
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
        self.enabled = bool(self.bot_token and self.channel_id)

        if self.enabled:
            print(f"[{self.platform_name}] Initialized")
        else:
            print(f"[{self.platform_name}] Disabled (missing credentials)")

    def publish(self, text: str, url: str = None, image_path: str = None):
        """Публикует пост в Telegram канал"""
        if not self.enabled:
            print(f"[{self.platform_name}] Skipped (not configured)")
            return None

        try:
            # Форматируем сообщение с Markdown
            message = text
            if url:
                message += f"\n\n🔗 Читать полностью: {url}"

            # Если есть изображение
            if image_path and os.path.exists(image_path):
                api_url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"

                with open(image_path, 'rb') as photo:
                    files = {'photo': photo}
                    data = {
                        'chat_id': self.channel_id,
                        'caption': message[:1024],  # Telegram limit
                        'parse_mode': 'Markdown'
                    }
                    response = requests.post(api_url, files=files, data=data, timeout=30)
            else:
                # Только текст
                api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                data = {
                    'chat_id': self.channel_id,
                    'text': message,
                    'parse_mode': 'Markdown',
                    'disable_web_page_preview': False
                }
                response = requests.post(api_url, data=data, timeout=30)

            response.raise_for_status()
            result = response.json()

            if result.get('ok'):
                message_id = result.get('result', {}).get('message_id')
                print(f"[{self.platform_name}] ✅ Published: {message_id}")
                return message_id
            else:
                print(f"[{self.platform_name}] ❌ Error: {result}")
                return None

        except Exception as e:
            print(f"[{self.platform_name}] ❌ Error: {e}")
            return None


class SocialMediaCoordinator:
    """Координатор для публикации во все социальные сети"""

    def __init__(self):
        self.publishers = {
            'facebook': FacebookPublisher(),
            'twitter': TwitterPublisher(),
            'threads': ThreadsPublisher(),
            'vk': VKPublisher(),
            'instagram': InstagramPublisher(),
            'telegram': TelegramPublisher()  # Добавлен Telegram
        }

        # Подсчитываем включенные платформы
        enabled_count = sum(1 for p in self.publishers.values() if p.is_enabled())
        print(f"\n[SocialMediaCoordinator] Initialized with {enabled_count}/6 platforms enabled")

    def publish_to_all(self, posts_data: dict, image_path: str = None):
        """
        Публикует во все настроенные социальные сети

        Args:
            posts_data: dict с данными постов для каждой платформы
                        Формат: {'facebook': {'text': '...', 'hashtags': [...], 'url': '...'}, ...}
            image_path: Путь к изображению (для Instagram)

        Returns:
            dict: Результаты публикаций для каждой платформы
        """
        results = {}

        print("\n" + "="*60)
        print("PUBLISHING TO SOCIAL MEDIA")
        print("="*60)

        for platform_name, publisher in self.publishers.items():
            if not publisher.is_enabled():
                results[platform_name] = {'success': False, 'reason': 'not_configured'}
                continue

            if platform_name not in posts_data:
                print(f"[{platform_name}] ⚠️ No post data provided")
                results[platform_name] = {'success': False, 'reason': 'no_data'}
                continue

            post_data = posts_data[platform_name]
            text = post_data.get('text', '')
            hashtags = post_data.get('hashtags', [])
            url = post_data.get('url')

            # Форматируем пост с хештегами
            from social_content_generator import SocialContentGenerator
            generator = SocialContentGenerator()
            formatted_text = generator.format_post_with_hashtags(
                text=text,
                hashtags=hashtags,
                url=url,
                platform=platform_name
            )

            try:
                # Публикуем
                post_id = publisher.publish(
                    text=formatted_text,
                    url=url,
                    image_path=image_path
                )

                if post_id:
                    results[platform_name] = {
                        'success': True,
                        'post_id': post_id,
                        'text': formatted_text[:100] + '...' if len(formatted_text) > 100 else formatted_text
                    }
                else:
                    results[platform_name] = {'success': False, 'reason': 'publish_failed'}

                # Задержка между публикациями
                time.sleep(2)

            except Exception as e:
                print(f"[{platform_name}] ❌ Exception: {e}")
                results[platform_name] = {'success': False, 'reason': str(e)}

        # Итоговый отчет
        successful = sum(1 for r in results.values() if r.get('success'))
        print("\n" + "="*60)
        print(f"PUBLICATION RESULTS: {successful}/{len(self.publishers)} successful")
        print("="*60)

        for platform, result in results.items():
            status = "✅" if result.get('success') else "❌"
            print(f"{status} {platform.upper()}: {result.get('post_id', result.get('reason', 'unknown'))}")

        print("="*60 + "\n")

        return results


def test_social_media_publishing():
    """Тестирование публикации в социальные сети"""
    print("Testing Social Media Publishing...")

    # Тестовые данные
    test_posts = {
        'facebook': {
            'text': 'Check out our latest article about AI!',
            'hashtags': ['AI', 'ArtificialIntelligence', 'Technology'],
            'url': 'https://thenextai.dev/test'
        },
        'twitter': {
            'text': 'New article about AI is live!',
            'hashtags': ['AI', 'Tech'],
            'url': 'https://thenextai.dev/test'
        },
        'threads': {
            'text': 'Just published a deep dive into AI. What do you think?',
            'hashtags': ['AI', 'Discussion', 'Tech'],
            'url': 'https://thenextai.dev/test'
        },
        'vk': {
            'text': 'Новая статья об искусственном интеллекте!',
            'hashtags': ['ИИ', 'Технологии', 'AI'],
            'url': 'https://thenextai.dev/test'
        },
        'instagram': {
            'text': 'Latest AI insights',
            'hashtags': ['AI', 'Tech', 'Innovation', 'Future', 'ArtificialIntelligence'],
            'url': 'https://thenextai.dev/test'
        }
    }

    coordinator = SocialMediaCoordinator()
    results = coordinator.publish_to_all(test_posts, image_path=None)

    return results


if __name__ == "__main__":
    test_social_media_publishing()
