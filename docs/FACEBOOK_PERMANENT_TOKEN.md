# 🔐 Facebook Permanent Token Setup

## Проблема

Facebook Page Tokens истекают через 60 дней, требуя мануальное обновление.

## ✅ Решение: Permanent Token через System User

Facebook позволяет создать **бессрочный токен**, который никогда не истекает.

---

## Метод 1: System User (Recommended)

### Шаг 1: Создать Facebook App (если еще нет)

1. Перейдите на https://developers.facebook.com/apps
2. Нажмите **Create App**
3. Выберите **Business** type
4. Заполните детали приложения

### Шаг 2: Создать Business Manager Account

1. Перейдите на https://business.facebook.com
2. Создайте Business Account (если еще нет)
3. Добавьте свою Facebook Page в Business Manager:
   - **Settings** → **Accounts** → **Pages**
   - Нажмите **Add** → выберите свою страницу

### Шаг 3: Создать System User

1. В Business Manager перейдите:
   - **Settings** → **Users** → **System Users**
2. Нажмите **Add**
3. Имя: `WordPress Auto Poster`
4. Role: **Admin**
5. Нажмите **Create System User**

### Шаг 4: Сгенерировать Permanent Token

1. Нажмите на созданного System User
2. Нажмите **Generate New Token**
3. Выберите ваше приложение
4. Выберите права (permissions):
   - ✅ `pages_show_list`
   - ✅ `pages_read_engagement`
   - ✅ `pages_manage_posts`
   - ✅ `pages_manage_engagement`
5. Token expiration: выберите **Never expire** (Никогда не истекает)
6. Нажмите **Generate Token**
7. **Скопируйте токен** (он больше не появится!)

### Шаг 5: Добавить Page Access для System User

1. В Business Manager:
   - **Settings** → **Accounts** → **Pages**
2. Выберите свою страницу
3. Нажмите **Assign Partner** или **Assign People**
4. Найдите ваш System User
5. Дайте права:
   - ✅ **Create content**
   - ✅ **Moderate content**
6. Сохраните

### Шаг 6: Получить Page Access Token

Теперь нужно обменять System User Token на Page Token:

```bash
# Замените:
# SYSTEM_USER_TOKEN - токен из шага 4
# PAGE_ID - ID вашей страницы

curl -X GET "https://graph.facebook.com/v18.0/PAGE_ID?fields=access_token&access_token=SYSTEM_USER_TOKEN"
```

**Ответ:**
```json
{
  "access_token": "EAAxxxxx...",  // ← Это ваш PERMANENT Page Token!
  "id": "632284956645073"
}
```

### Шаг 7: Обновить .env

```bash
FACEBOOK_PAGE_ID=632284956645073
FACEBOOK_ACCESS_TOKEN=EAAxxxxx...  # ← Permanent token из шага 6
```

✅ **Готово!** Этот токен **никогда не истечет**.

---

## Метод 2: Автоматическое обновление Long-lived Token

Если не хотите использовать System User, можно автоматизировать обновление.

### Создать скрипт обновления

```python
#!/usr/bin/env python3
"""
Автоматическое обновление Facebook Page Token
"""
import os
import requests
from dotenv import load_dotenv, set_key

load_dotenv()

def refresh_facebook_token():
    """Обновляет Facebook Page Token"""

    # Данные из .env
    app_id = os.getenv('FACEBOOK_APP_ID')
    app_secret = os.getenv('FACEBOOK_APP_SECRET')
    current_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
    page_id = os.getenv('FACEBOOK_PAGE_ID')

    if not all([app_id, app_secret, current_token, page_id]):
        print("❌ Отсутствуют необходимые credentials в .env")
        return False

    try:
        # Шаг 1: Обмен на long-lived User Token
        print("🔄 Обмен на long-lived User Token...")
        exchange_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': app_id,
            'client_secret': app_secret,
            'fb_exchange_token': current_token
        }

        response = requests.get(exchange_url, params=params)
        response.raise_for_status()

        long_lived_user_token = response.json().get('access_token')
        print(f"✅ Получен long-lived User Token")

        # Шаг 2: Получить Page Token из User Token
        print("🔄 Получение Page Token...")
        accounts_url = f"https://graph.facebook.com/v18.0/me/accounts"
        params = {'access_token': long_lived_user_token}

        response = requests.get(accounts_url, params=params)
        response.raise_for_status()

        pages = response.json().get('data', [])

        # Найти нужную страницу
        page_token = None
        for page in pages:
            if page['id'] == page_id:
                page_token = page['access_token']
                break

        if not page_token:
            print(f"❌ Страница {page_id} не найдена")
            return False

        print(f"✅ Получен новый Page Token")

        # Шаг 3: Обновить .env файл
        env_file = '.env'
        set_key(env_file, 'FACEBOOK_ACCESS_TOKEN', page_token)

        print(f"✅ Token обновлен в .env файле")
        print(f"📅 Действителен ~60 дней")

        return True

    except Exception as e:
        print(f"❌ Ошибка обновления токена: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("   ОБНОВЛЕНИЕ FACEBOOK PAGE TOKEN")
    print("="*60)
    print()

    success = refresh_facebook_token()

    if success:
        print()
        print("🎉 Токен успешно обновлен!")
    else:
        print()
        print("❌ Не удалось обновить токен")
```

### Добавить в .env

```bash
# Facebook App credentials для автообновления токена
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
```

### Настроить автоматический запуск (cron)

```bash
# Запускать каждые 50 дней
# crontab -e

# Каждые 50 дней в 3:00 утра
0 3 */50 * * cd /path/to/wordpress-auto-poster && python refresh_facebook_token.py
```

---

## Метод 3: Session-Based подход (как Instagram)

К сожалению, для Facebook нет надежной библиотеки как `instagrapi`. Но есть альтернативы:

### facebook-sdk с сохранением сессии

```python
import facebook
import pickle
from pathlib import Path

class FacebookSessionPublisher:
    """Facebook publisher с сохранением сессии"""

    def __init__(self):
        self.session_file = '.facebook_session.pkl'
        self.graph = None

    def load_session(self):
        """Загрузить сохраненную сессию"""
        session_path = Path(self.session_file)
        if session_path.exists():
            try:
                with open(session_path, 'rb') as f:
                    token_data = pickle.load(f)

                # Проверка валидности
                self.graph = facebook.GraphAPI(token_data['access_token'])
                self.graph.get_object('me')  # Test

                return True
            except:
                return False
        return False

    def save_session(self, access_token):
        """Сохранить сессию"""
        with open(self.session_file, 'wb') as f:
            pickle.dump({'access_token': access_token}, f)
```

**Проблема:** Facebook токены все равно истекают, это не решает проблему полностью.

---

## 🎯 Рекомендация

### Лучшее решение: System User + Permanent Token

**Преимущества:**
- ✅ Токен **никогда не истекает**
- ✅ Нулевое обслуживание
- ✅ Официальный метод Facebook
- ✅ Надежный

**Недостатки:**
- ⚠️ Требует Business Manager (бесплатно)
- ⚠️ Настройка занимает 10-15 минут

### Альтернатива: Автоматическое обновление

Если не хотите Business Manager:
- ✅ Автоматизация через cron
- ✅ Обновление каждые 50 дней
- ⚠️ Требует App ID + App Secret

### Не рекомендуется: Ручное обновление

- ❌ Каждые 60 дней вручную
- ❌ Риск пропустить обновление
- ❌ Downtime публикаций

---

## Сравнение методов

| Метод | Срок жизни | Автоматизация | Сложность | Рекомендация |
|-------|-----------|---------------|-----------|--------------|
| **System User** | ♾️ Бессрочно | Не требуется | Средняя | ⭐⭐⭐⭐⭐ |
| **Auto-refresh** | 60 дней | Cron job | Низкая | ⭐⭐⭐⭐ |
| **Manual refresh** | 60 дней | Нет | Низкая | ⭐⭐ |
| **Graph API Explorer** | 1-2 часа | Нет | Очень низкая | ⭐ |

---

## Проверка токена

### Проверить тип и срок действия

```bash
curl -X GET "https://graph.facebook.com/v18.0/debug_token?input_token=YOUR_TOKEN&access_token=YOUR_TOKEN"
```

**Ответ:**
```json
{
  "data": {
    "app_id": "123456",
    "type": "PAGE",  // ← Должен быть PAGE
    "is_valid": true,
    "expires_at": 0,  // ← 0 = бессрочный!
    "data_access_expires_at": 1234567890
  }
}
```

**`expires_at: 0`** = токен бессрочный ✅

---

## Готово! 🎉

После настройки Permanent Token у вас будет:
- ✅ Facebook токен, который **никогда не истечет**
- ✅ Нулевое обслуживание
- ✅ Надежная автоматическая публикация

---

## Следующие шаги

1. **Создать System User** (10 минут)
2. **Получить Permanent Token**
3. **Обновить .env**
4. **Запустить тест:**
   ```bash
   python -c "from social_media_clients import FacebookPublisher; p = FacebookPublisher(); p.publish('Test', 'https://test.com')"
   ```

5. **Проверить что токен бессрочный:**
   ```bash
   # Должно показать expires_at: 0
   curl "https://graph.facebook.com/v18.0/debug_token?input_token=YOUR_TOKEN&access_token=YOUR_TOKEN"
   ```

---

**Happy permanent token! 🚀**
