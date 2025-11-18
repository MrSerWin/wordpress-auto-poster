#!/usr/bin/env python3
"""
Генератор контента для социальных сетей
Создает краткие саммари статей с хештегами для каждой соцсети
"""
import time
import re
import json
from gemini_client import GeminiClient


class SocialContentGenerator:
    """Генератор контента для публикаций в социальных сетях"""

    def __init__(self):
        self.client = GeminiClient()

    def generate_social_posts(self, article_title: str, article_url: str, article_content: str = "", keywords: list = None):
        """
        Генерирует посты для всех социальных сетей

        Args:
            article_title: Заголовок статьи
            article_url: URL опубликованной статьи
            article_content: Содержимое статьи (опционально, для лучшего саммари)
            keywords: Ключевые слова статьи

        Returns:
            dict: Посты для каждой социальной сети
        """
        if not self.client.client:
            print("[social_content] Gemini client not available, using fallback")
            return self._generate_fallback_posts(article_title, article_url, keywords)

        try:
            # Подготовка промпта
            keywords_str = ", ".join(keywords) if keywords else "AI, technology"
            content_preview = article_content[:500] if article_content else ""

            prompt = f"""You are a social media marketing expert. Create engaging social media posts for an article.

ARTICLE INFO:
Title: {article_title}
URL: {article_url}
Keywords: {keywords_str}
Content preview: {content_preview}

TASK: Create social media posts for different platforms with these requirements:

1. FACEBOOK:
   - Length: 200-250 characters
   - Include engaging summary
   - Add 3-5 relevant hashtags
   - Include call-to-action
   - Professional tone

2. TWITTER/X:
   - Length: Maximum 270 characters (leave room for URL)
   - Concise and impactful
   - Add 2-3 hashtags
   - Engaging hook

3. THREADS:
   - Length: 300-400 characters
   - Conversational tone
   - Add 3-4 hashtags
   - Encourage discussion

4. VK:
   - Length: 200-300 characters
   - Russian-speaking audience focus
   - Add 4-6 hashtags
   - Engaging and informative

5. INSTAGRAM:
   - Length: 150-200 characters for caption
   - Visual-focused description
   - Add 5-8 hashtags
   - Emoji-friendly but professional

6. TELEGRAM:
   - Length: 300-500 characters
   - Clear and informative
   - Add 3-5 hashtags
   - Can use bold and italic formatting
   - Tech-savvy audience

IMPORTANT OUTPUT FORMAT:
Return ONLY valid JSON with this EXACT structure (no markdown, no code blocks):
{{
    "facebook": {{
        "text": "Engaging post text here",
        "hashtags": ["hashtag1", "hashtag2", "hashtag3"]
    }},
    "twitter": {{
        "text": "Tweet text here",
        "hashtags": ["hashtag1", "hashtag2"]
    }},
    "threads": {{
        "text": "Threads post text here",
        "hashtags": ["hashtag1", "hashtag2", "hashtag3"]
    }},
    "vk": {{
        "text": "VK post text here",
        "hashtags": ["hashtag1", "hashtag2", "hashtag3"]
    }},
    "instagram": {{
        "text": "Instagram caption here",
        "hashtags": ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5"]
    }},
    "telegram": {{
        "text": "Telegram message here",
        "hashtags": ["hashtag1", "hashtag2", "hashtag3"]
    }}
}}

HASHTAG RULES:
- Use topic-relevant hashtags
- Mix popular and niche hashtags
- Include "AI", "ArtificialIntelligence", "Technology" when relevant
- NO spaces in hashtags
- Capitalize words in hashtags for readability (e.g., #ArtificialIntelligence)

Generate the posts now as valid JSON ONLY:"""

            # Генерируем контент с retry logic
            from google.genai.types import GenerateContentConfig

            def make_request():
                return self.client.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=GenerateContentConfig(
                        temperature=0.9,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=2048,
                    )
                )

            response = self.client._make_api_request_with_retry(make_request)
            response_text = response.text.strip()

            # Парсим JSON

            # Удаляем markdown code blocks если есть
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Ищем JSON напрямую
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_text

            posts = json.loads(json_str)

            # Валидация структуры
            required_platforms = ['facebook', 'twitter', 'threads', 'vk', 'instagram', 'telegram']
            for platform in required_platforms:
                if platform not in posts:
                    print(f"[social_content] Warning: Missing {platform} in response")
                    posts[platform] = self._get_fallback_post(platform, article_title, keywords)
                elif 'text' not in posts[platform] or 'hashtags' not in posts[platform]:
                    print(f"[social_content] Warning: Invalid structure for {platform}")
                    posts[platform] = self._get_fallback_post(platform, article_title, keywords)

            # Добавляем URL к каждому посту
            for platform in posts:
                if 'url' not in posts[platform]:
                    posts[platform]['url'] = article_url

            print(f"[social_content] Generated posts for all platforms")
            return posts

        except json.JSONDecodeError as e:
            print(f"[social_content] JSON parsing error: {e}")
            print(f"[social_content] Response was: {response_text[:200]}...")
            return self._generate_fallback_posts(article_title, article_url, keywords)
        except Exception as e:
            print(f"[social_content] Error generating social posts: {e}")
            return self._generate_fallback_posts(article_title, article_url, keywords)

    def _get_fallback_post(self, platform: str, title: str, keywords: list = None):
        """Генерирует fallback пост для платформы"""
        hashtags = keywords[:3] if keywords else ["AI", "Technology", "Innovation"]

        templates = {
            'facebook': {
                'text': f"Check out our latest article: {title}! Learn more about AI and technology trends.",
                'hashtags': hashtags + ["ArtificialIntelligence", "TechNews"]
            },
            'twitter': {
                'text': f"New article: {title}",
                'hashtags': hashtags[:2] + ["AI"]
            },
            'threads': {
                'text': f"Just published: {title}. What are your thoughts on this topic?",
                'hashtags': hashtags + ["Discussion"]
            },
            'vk': {
                'text': f"Новая статья: {title}. Читайте на нашем сайте!",
                'hashtags': hashtags + ["ИИ", "Технологии"]
            },
            'instagram': {
                'text': f"New: {title}",
                'hashtags': hashtags + ["AI", "Tech", "Innovation", "Future"]
            },
            'telegram': {
                'text': f"📰 **{title}**\n\nЧитайте полный анализ на нашем сайте!",
                'hashtags': hashtags + ["Tech", "AI"]
            }
        }

        return templates.get(platform, {'text': title, 'hashtags': hashtags})

    def _generate_fallback_posts(self, title: str, url: str, keywords: list = None):
        """Генерирует fallback посты для всех платформ"""
        posts = {}
        for platform in ['facebook', 'twitter', 'threads', 'vk', 'instagram', 'telegram']:
            posts[platform] = self._get_fallback_post(platform, title, keywords)
            posts[platform]['url'] = url

        print(f"[social_content] Generated fallback posts for all platforms")
        return posts

    def format_post_with_hashtags(self, text: str, hashtags: list, url: str = None, platform: str = 'facebook'):
        """
        Форматирует финальный пост с текстом, хештегами и ссылкой

        Args:
            text: Основной текст поста
            hashtags: Список хештегов
            url: URL для добавления
            platform: Платформа для правильного форматирования

        Returns:
            str: Отформатированный пост
        """
        # Форматируем хештеги - убираем пробелы и специальные символы
        formatted_hashtags = []
        for tag in hashtags:
            # Убираем # если есть
            clean_tag = tag.strip('#').strip()
            # Убираем пробелы и заменяем на пустоту (camelCase стиль)
            # или можно заменить на подчеркивание: clean_tag = clean_tag.replace(' ', '_')
            clean_tag = clean_tag.replace(' ', '')
            # Убираем другие недопустимые символы
            clean_tag = re.sub(r'[^\w]', '', clean_tag)
            if clean_tag:  # Добавляем только непустые теги
                formatted_hashtags.append(f"#{clean_tag}")

        hashtag_string = " ".join(formatted_hashtags)

        # Разные форматы для разных платформ
        if platform == 'twitter':
            # Twitter: текст + хештеги + URL (URL автоматически сокращается)
            return f"{text}\n\n{hashtag_string}\n{url}" if url else f"{text}\n\n{hashtag_string}"

        elif platform == 'instagram':
            # Instagram: текст, потом хештеги блоком
            return f"{text}\n.\n.\n.\n{hashtag_string}\n{url}" if url else f"{text}\n.\n.\n.\n{hashtag_string}"

        elif platform == 'vk':
            # VK: текст + хештеги + URL
            return f"{text}\n\n{hashtag_string}\n\n{url}" if url else f"{text}\n\n{hashtag_string}"

        else:  # facebook, threads и другие
            # Стандартный формат
            return f"{text}\n\n{hashtag_string}\n\n{url}" if url else f"{text}\n\n{hashtag_string}"


def test_social_content_generator():
    """Тестирование генератора контента"""
    print("Testing Social Content Generator...")

    generator = SocialContentGenerator()

    # Тестовые данные
    test_article = {
        'title': 'AI Answers Your Burning Questions - Part 2: Deep Dive',
        'url': 'https://thenextai.dev/ai-answers-deep-dive',
        'keywords': ['AI', 'ArtificialIntelligence', 'MachineLearning', 'Technology'],
        'content': 'Explore the latest developments in AI technology...'
    }

    # Генерируем посты
    posts = generator.generate_social_posts(
        article_title=test_article['title'],
        article_url=test_article['url'],
        article_content=test_article['content'],
        keywords=test_article['keywords']
    )

    # Выводим результаты
    print("\n" + "="*60)
    for platform, post_data in posts.items():
        print(f"\n{platform.upper()}:")
        print("-" * 60)
        formatted = generator.format_post_with_hashtags(
            text=post_data['text'],
            hashtags=post_data['hashtags'],
            url=post_data['url'],
            platform=platform
        )
        print(formatted)
        print(f"\nLength: {len(formatted)} characters")
    print("="*60)


if __name__ == "__main__":
    test_social_content_generator()
