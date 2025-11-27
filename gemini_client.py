"""gemini_client.py

Real implementation of Gemini API integration for article and image generation.
"""
import os
import re
import json
import time
from dotenv import load_dotenv
load_dotenv()

# Try to import Google GenAI SDK
try:
    import google.genai as genai
    from google.genai.types import GenerateContentConfig, GoogleSearch
    HAS_GENAI = True
except Exception as e:
    print(f"[gemini_client] Warning: google.genai SDK import failed: {e}")
    HAS_GENAI = False

class GeminiClient:
    def __init__(self):
        # Try multiple environment variable names for API key
        self.api_key = (os.getenv('GOOGLE_API_KEY') or
                       os.getenv('GEMINI_API_KEY') or
                       "KEY")

        if not HAS_GENAI:
            print("[gemini_client] Warning: google.genai SDK not installed. Using local stubs.")
            self.client = None
            return

        if not self.api_key:
            print("[gemini_client] Warning: No API key found. Using local stubs.")
            self.client = None
            return

        # Initialize real client
        self.client = genai.Client(api_key=self.api_key)
        print("[gemini_client] Initialized with Gemini API")

        # Rate limiting: track last request time
        self.last_request_time = 0
        self.min_request_interval = 2.0  # минимум 2 секунды между запросами

    def _wait_for_rate_limit(self):
        """Enforce rate limiting between API requests"""
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            print(f"[gemini_client] Rate limiting: waiting {sleep_time:.1f}s before next request")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _make_api_request_with_retry(self, request_func, max_retries=3):
        """Make API request with exponential backoff retry on 429 errors"""
        for attempt in range(max_retries):
            try:
                self._wait_for_rate_limit()
                return request_func()
            except Exception as e:
                error_str = str(e)
                # Check for 429 error
                if "429" in error_str or "Too Many Requests" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    # Try to extract retry delay from error message
                    import re
                    retry_match = re.search(r'retry in ([\d.]+)s', error_str)

                    if retry_match:
                        # API tells us exact time to wait
                        suggested_wait = float(retry_match.group(1))
                        # Add 1 second buffer
                        wait_time = suggested_wait + 1
                        print(f"[gemini_client] ⚠️ Quota exceeded. API suggests waiting {suggested_wait:.1f}s")
                        print(f"[gemini_client] ⏳ Waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}...")
                    else:
                        # Exponential backoff: 10s, 30s, 60s
                        wait_time = 10 * (3 ** attempt)
                        print(f"[gemini_client] ⚠️ Rate limit hit (429). Retry {attempt + 1}/{max_retries} after {wait_time}s...")

                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"[gemini_client] ❌ Rate limit exceeded after {max_retries} retries")
                        print(f"[gemini_client] 💡 TIP: You may have exceeded your API quota. Check: https://ai.dev/usage?tab=rate-limit")
                        raise
                else:
                    # Not a rate limit error, re-raise immediately
                    raise
        return None

    def generate_article(self, brief_plan: str, seo_focus: str = "", tone="informative", word_count=900):
        """Generate a full article using Gemini API with SEO optimization"""

        if not self.client:
            # Fallback to placeholder
            return self._generate_placeholder_article(brief_plan, seo_focus)

        try:
            # Create a detailed prompt for article generation
            prompt = f"""You are a professional content writer specializing in AI and technology topics.

Write a comprehensive, SEO-optimized blog article with the following requirements:

TOPIC: {brief_plan}
SEO FOCUS: {seo_focus if seo_focus else brief_plan}
TONE: {tone}
TARGET LENGTH: {word_count} words

REQUIREMENTS:
1. Write a compelling, engaging article that provides real value to readers
2. Use a clear structure with H2 and H3 headings
3. Include practical examples and insights
4. Optimize for SEO with natural keyword usage
5. Write in an accessible, conversational style
6. Include a strong introduction and conclusion
7. Format in HTML with proper tags (h2, h3, p, ul, ol, strong, em)

CRITICAL OUTPUT FORMAT RULES:
- You MUST return ONLY a valid JSON object
- Do NOT include any text before or after the JSON
- Do NOT wrap the JSON in markdown code blocks
- The JSON must be properly formatted and parseable
- All field values must be strings or arrays of strings (no nested objects)

Return your response as a valid JSON object with this EXACT structure:
{{
    "title": "Compelling article title (60-70 characters max, SEO-optimized, NO special chars like {{}}, [], quotes)",
    "slug": "url-friendly-slug-for-wordpress",
    "meta_description": "Engaging meta description (150-160 characters, describes article value)",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "content_html": "Full HTML article content with proper tags (minimum 500 words)",
    "image_prompt": "Detailed prompt for AI image generation (one sentence describing a relevant, professional image)",
    "headings_summary": ["List of main H2 headings used"]
}}

IMPORTANT FIELD REQUIREMENTS:
- "title": Must be 10-70 characters, plain text, NO JSON syntax characters
- "slug": Must be lowercase, hyphens only, 5-100 characters
- "keywords": Array of 3-10 simple keywords (each 1-3 words max, NO sentences)
- "content_html": Must be valid HTML, minimum 500 characters, NO raw JSON
- "meta_description": Must be 50-160 characters

The article should be comprehensive, interesting, with examples of available resources or solutions, and compel the reader to return to the site. Article MUST be in English.

Write the article now as valid JSON ONLY:"""

            # Generate content using Gemini with retry logic
            def make_request():
                return self.client.models.generate_content(
                    # model='gemini-2.0-flash-exp',
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=GenerateContentConfig(
                        temperature=0.8,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=8192,
                    )
                )

            response = self._make_api_request_with_retry(make_request)

            # Extract the text response
            response_text = response.text.strip()

            # Try to extract JSON from the response
            # Sometimes Gemini wraps JSON in markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON directly
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_text

            # Parse JSON
            article_data = json.loads(json_str)

            # Validate required fields
            required_fields = ['title', 'slug', 'meta_description', 'keywords', 'content_html', 'image_prompt']
            for field in required_fields:
                if field not in article_data:
                    article_data[field] = self._get_fallback_value(field, brief_plan)

            print(f"[gemini_client] Article generated: {article_data['title'][:50]}...")
            return article_data

        except json.JSONDecodeError as e:
            print(f"[gemini_client] JSON parsing error: {e}")
            print(f"[gemini_client] Response was: {response_text[:200]}...")
            # Return a structured article from the text
            return self._parse_unstructured_response(response_text, brief_plan, seo_focus)
        except Exception as e:
            print(f"[gemini_client] Error generating article: {e}")
            return self._generate_placeholder_article(brief_plan, seo_focus)

    def _generate_placeholder_article(self, _brief_plan, _seo_focus):
        """Generate a simple placeholder article"""
        print(f"[gemini_client] WARNING: Falling back to placeholder, returning None to prevent bad article")
        # Return None instead of publishing placeholder content
        return None

    def _get_fallback_value(self, field, brief_plan):
        """Get fallback value for missing fields"""
        fallbacks = {
            'title': brief_plan,
            'slug': brief_plan.lower().replace(' ', '-')[:50],
            'meta_description': f"Article about {brief_plan}",
            'keywords': ["AI", "technology"],
            'content_html': f"<p>Content about {brief_plan}</p>",
            'image_prompt': f"Illustration for {brief_plan}",
            'headings_summary': []
        }
        return fallbacks.get(field, '')

    def _parse_unstructured_response(self, _text, _brief_plan, _seo_focus):
        """Try to extract article components from unstructured text"""
        print(f"[gemini_client] WARNING: Unstructured response detected, returning None to prevent bad article")
        # Return None instead of publishing malformed content
        return None

    def generate_image(self, image_prompt: str, size="1600x900"):
        """Generate image using Gemini API with 16:9 aspect ratio"""

        if not self.client:
            print("[gemini_client] No client available, using fallback image generation")
            return self._generate_fallback_image(image_prompt)

        try:
            from google.genai.types import Content, Part, GenerateContentConfig

            # Create content for image generation
            contents = [
                Content(
                    role="user",
                    parts=[
                        Part.from_text(text=f"Generate a professional, high-quality image for a blog article. {image_prompt}. The image should be visually appealing, modern, and relevant to the content. Highly detailed, sharp focus, 4K resolution. Aspect Ratio 16:9")
                    ],
                ),
            ]

            # Configure image generation
            generate_content_config = GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            )

            print(f"[gemini_client] Generating image with Gemini API for prompt: {image_prompt[:100]}...")

            # Generate content using streaming with retry logic
            def make_image_request():
                result = []
                for chunk in self.client.models.generate_content_stream(
                    model="gemini-2.5-flash-image",  # Правильное название модели
                    contents=contents,
                    config=generate_content_config,
                ):
                    result.append(chunk)
                return result

            chunks = self._make_api_request_with_retry(make_image_request)

            for chunk in chunks:
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue
                    
                if (chunk.candidates[0].content.parts[0].inline_data and 
                    chunk.candidates[0].content.parts[0].inline_data.data):
                    
                    inline_data = chunk.candidates[0].content.parts[0].inline_data
                    data_buffer = inline_data.data
                    mime_type = inline_data.mime_type
                    
                    print(f"[gemini_client] Image generated successfully via Gemini API")
                    return data_buffer, mime_type

            # If no image was generated in the stream
            print("[gemini_client] No image generated in stream, using fallback")
            return self._generate_fallback_image(image_prompt)

        except Exception as e:
            print(f"[gemini_client] Error generating image with Gemini API: {e}")
            return self._generate_fallback_image(image_prompt)

    def _generate_fallback_image(self, image_prompt: str):
        """Generate a fallback image when Gemini API is not available"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io

            # Create a nice gradient background with 16:9 aspect ratio
            img = Image.new('RGB', (1600, 900), color=(45, 55, 72))
            draw = ImageDraw.Draw(img)

            # Add gradient effect
            for i in range(900):
                color = (45 + i//15, 55 + i//20, 72 + i//15)
                draw.line([(0, i), (1600, i)], fill=color)

            # Add text
            text = image_prompt
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
            except:
                font = ImageFont.load_default()

            # Center text
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (1600 - text_width) // 2
            y = (900 - text_height) // 2

            draw.text((x, y), text, fill=(255, 255, 255), font=font)

            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            print(f"[gemini_client] Generated fallback image with 16:9 aspect ratio")
            return img_bytes.read(), 'image/png'

        except Exception as e:
            print(f"[gemini_client] Error creating fallback image: {e}")
            return self._get_placeholder_image()

    def _extract_keywords_from_prompt(self, prompt: str):
        """Extract relevant keywords from image prompt"""
        # Remove common words
        stop_words = {'a', 'an', 'the', 'for', 'to', 'of', 'in', 'on', 'at', 'and', 'or', 'with', 'about'}
        words = prompt.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords[:5] if keywords else ['technology', 'ai', 'digital']

    def _get_placeholder_image(self):
        """Return a simple placeholder image"""
        import base64
        placeholder = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAn8B9o4pJwAAAABJRU5ErkJggg=='
        )
        return placeholder, 'image/png'
    

def validate_article(article: dict, _topic: str) -> tuple[bool, str]:
    """
    Validate article quality before publishing
    Returns: (is_valid, error_message)
    """
    if not article:
        return False, "Article is None or empty"

    # Check title
    title = article.get("title", "")
    if not title or len(title) < 10:
        return False, "Title is missing or too short"
    if len(title) > 200:
        return False, "Title is too long (max 200 chars)"
    # Check if title contains JSON-like syntax
    if "{" in title or "}" in title or "[" in title or "]" in title:
        return False, "Title contains JSON syntax - malformed response"

    # Check slug
    slug = article.get("slug", "")
    if not slug or len(slug) < 5:
        return False, "Slug is missing or too short"

    # Check content
    content = article.get("content_html", "")
    if not content or len(content) < 100:
        return False, "Content is missing or too short (min 100 chars)"
    # Check if content is just JSON
    if content.strip().startswith("{") and content.strip().endswith("}"):
        return False, "Content appears to be raw JSON - malformed response"
    # Check for placeholder text
    if "placeholder" in content.lower() or "lorem ipsum" in content.lower():
        return False, "Content contains placeholder text"

    # Check keywords
    keywords = article.get("keywords", [])
    if not keywords or not isinstance(keywords, list):
        return False, "Keywords are missing or invalid"
    if len(keywords) < 2:
        return False, "Not enough keywords (min 2)"
    # Check each keyword is a proper string (not a sentence)
    for keyword in keywords:
        if not isinstance(keyword, str) or len(keyword) > 50:
            return False, f"Invalid keyword format: {keyword}"
        if "\n" in keyword or len(keyword.split()) > 5:
            return False, f"Keyword is too long or contains newlines: {keyword}"

    # Check meta description
    meta = article.get("meta_description", "")
    if not meta or len(meta) < 50:
        return False, "Meta description is missing or too short"

    # Check image prompt
    image_prompt = article.get("image_prompt", "")
    if not image_prompt or len(image_prompt) < 10:
        return False, "Image prompt is missing or too short"

    print(f"[validate_article] Article validation passed for: {title[:50]}...")
    return True, ""


def generate_article_with_image(topic: str):
    """Wrapper: возвращает словарь с title, content, image_url"""
    client = GeminiClient()

    # 1️⃣ Генерируем текст статьи
    article = client.generate_article(brief_plan=topic, seo_focus=topic)

    # VALIDATE: Check if article generation failed
    if not article:
        print(f"[generate_article_with_image] ERROR: Article generation returned None for topic: {topic}")
        return None

    # VALIDATE: Check article quality
    is_valid, error_msg = validate_article(article, topic)
    if not is_valid:
        print(f"[generate_article_with_image] ERROR: Article validation failed: {error_msg}")
        print(f"[generate_article_with_image] Article data: {article}")
        return None

    # 2️⃣ Генерируем изображение через Gemini API
    # Добавляем дополнительную задержку перед генерацией изображения
    print(f"[generate_article_with_image] Waiting 3 seconds before generating image...")
    time.sleep(3)

    image_prompt = article.get("image_prompt", f"Professional illustration for article about {topic}")
    image_bytes, mime_type = client.generate_image(image_prompt)

    # Сохраняем изображение локально
    import os
    import hashlib
    os.makedirs("generated_images", exist_ok=True)

    # Определяем расширение файла на основе MIME типа
    if mime_type == 'image/jpeg':
        extension = '.jpg'
    elif mime_type == 'image/png':
        extension = '.png'
    else:
        extension = '.png'  # по умолчанию PNG

    # уникальное имя файла
    fname = hashlib.md5(topic.encode()).hexdigest() + extension
    path = os.path.join("generated_images", fname)
    with open(path, "wb") as f:
        f.write(image_bytes)

    print(f"[generate_article_with_image] Image saved to: {path}")
    print(f"[generate_article_with_image] Article validated and ready to publish: {article['title'][:50]}...")

    # 3️⃣ Возвращаем словарь с нужными полями
    return {
        "title": article["title"],
        "content": article["content_html"],
        "image_url": path,  # локальный путь к изображению
        "keywords": article.get("keywords", []),
        "slug": article.get("slug", ""),
        "meta_description": article.get("meta_description", ""),
        "image_prompt": image_prompt
    }
