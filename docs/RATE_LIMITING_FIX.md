# Исправление ошибки 429 "Too Many Requests"

## Проблема
Получали ошибку от Gemini API:
```
HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent "HTTP/1.1 429 Too Many Requests"
```

**Детальная ошибка**:
```
Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests
Please retry in X seconds
```

## Причина
Код делал слишком много запросов к API без задержек:
1. Запрос на генерацию статьи
2. Сразу запрос на генерацию изображения
3. Превышение лимита RPM (Requests Per Minute)

## Решение

### 1. Добавлен Rate Limiting
В `gemini_client.py`:
- Минимум 2 секунды между любыми запросами к API
- Автоматическое отслеживание времени последнего запроса
- Принудительная задержка при необходимости

```python
def _wait_for_rate_limit(self):
    """Enforce rate limiting between API requests"""
    time_since_last = time.time() - self.last_request_time
    if time_since_last < self.min_request_interval:
        sleep_time = self.min_request_interval - time_since_last
        print(f"[gemini_client] Rate limiting: waiting {sleep_time:.1f}s before next request")
        time.sleep(sleep_time)
    self.last_request_time = time.time()
```

### 2. Добавлен Умный Exponential Backoff
При получении ошибки 429 код автоматически:
1. **Извлекает рекомендованное время ожидания** из ответа API
2. **Ждет именно столько, сколько рекомендует API** (+ 1 секунду буфера)
3. Если API не указал время, использует экспоненциальную задержку:
   - **Попытка 1**: Ждем 10 секунд
   - **Попытка 2**: Ждем 30 секунд
   - **Попытка 3**: Ждем 60 секунд
4. После 3 попыток - возвращаем ошибку с подсказкой

```python
def _make_api_request_with_retry(self, request_func, max_retries=3):
    for attempt in range(max_retries):
        try:
            self._wait_for_rate_limit()
            return request_func()
        except Exception as e:
            if "429" in str(e):
                wait_time = 5 * (3 ** attempt)  # 5s, 15s, 45s
                time.sleep(wait_time)
```

### 3. Дополнительная задержка между генерацией статьи и изображения
3 секунды между запросами для гарантии.

## Как использовать

### Обычный режим (автоматически обрабатывает лимиты)
```bash
python auto_publisher.py --publish-now
```

### Тестирование rate limiting
```bash
python test_rate_limits.py
```

## Рекомендации

### 1. Проверка лимитов API ⚠️ ВАЖНО

**Бесплатный tier Gemini имеет ограничения**:
- ❌ **15 RPM** (requests per minute) - 15 запросов в минуту
- ❌ **1,500 RPD** (requests per day) - 1,500 запросов в день
- ❌ **Ограничение токенов** - лимит на количество обработанных токенов

**Что делать если достигли лимита**:

1. **Проверьте текущее использование**:
   - Откройте: https://ai.dev/usage?tab=rate-limit
   - Посмотрите сколько запросов использовано

2. **Дождитесь сброса квоты**:
   - Квота RPM сбрасывается каждую минуту
   - Квота RPD сбрасывается в полночь UTC
   - **Рекомендация**: Подождите 1-2 минуты перед повторной попыткой

3. **Обновите API ключ** (если нужно больше лимитов):
   - Создайте новый проект: https://console.cloud.google.com/
   - Включите Gemini API
   - Создайте новый API ключ
   - Обновите `.env` файл с новым ключом

4. **Рассмотрите платный план**:
   - Pay-as-you-go план: значительно выше лимиты
   - Проверьте цены: https://ai.google.dev/pricing

### 2. Настройка интервалов
Если ошибки продолжаются, увеличьте задержки в `gemini_client.py`:

```python
self.min_request_interval = 5.0  # Увеличить до 5 секунд
```

### 3. Мониторинг логов
Следите за сообщениями:
- `[gemini_client] Rate limiting: waiting...` - нормально
- `[gemini_client] ⚠️ Rate limit hit (429)` - достигнут лимит, идет retry
- `[gemini_client] ❌ Rate limit exceeded` - лимит не преодолен после retries

### 4. Оптимизация публикации
В `auto_publisher.py` уже настроено:
- Публикация каждые 3 дня (не чаще)
- При ошибке - повторная попытка через 1 час

## Проверка работы

1. **Запустите тест**:
   ```bash
   python test_rate_limits.py
   ```

2. **Публикуйте одну статью**:
   ```bash
   python auto_publisher.py --publish-now
   ```

3. **Проверьте логи**:
   ```bash
   tail -f auto_publisher.log
   ```

## Ожидаемое поведение

✅ **Правильно**:
```
[gemini_client] Initialized with Gemini API
[gemini_client] Rate limiting: waiting 2.0s before next request
[gemini_client] Article generated: ...
[gemini_client] Waiting 3 seconds before generating image...
[gemini_client] Rate limiting: waiting 0.5s before next request
[gemini_client] Image generated successfully
```

❌ **Если всё ещё получаете 429**:

1. **Подождите 1-2 минуты** - квота RPM сбрасывается каждую минуту
2. **Проверьте использование**:
   ```bash
   # Откройте в браузере
   https://ai.dev/usage?tab=rate-limit
   ```
3. **Убедитесь, что не запущено несколько экземпляров**:
   ```bash
   ps aux | grep auto_publisher
   # Если есть старые процессы, убейте их:
   # kill -9 <PID>
   ```
4. **Проверьте нет ли других приложений с тем же API ключом**
5. **Увеличьте интервал между публикациями** в `auto_publisher.py`:
   ```python
   PUBLISH_INTERVAL_DAYS = 7  # Публиковать раз в неделю вместо раз в 3 дня
   ```

## Структура изменений

Файлы изменены:
- ✅ `gemini_client.py` - добавлен rate limiting и retry logic
- ✅ `test_rate_limits.py` - новый файл для тестирования
- ✅ `RATE_LIMITING_FIX.md` - эта документация

## Поддержка

Если проблема не решена:
1. Проверьте логи: `auto_publisher.log`
2. Запустите тест: `python test_rate_limits.py`
3. Увеличьте задержки в коде
4. Проверьте квоты API: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
