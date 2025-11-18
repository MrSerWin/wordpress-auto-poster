#!/usr/bin/env python3
"""
Диагностика и исправление проблем с Facebook API
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def check_facebook_token():
    """Проверить токен Facebook и получить правильный Page Token"""

    access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
    page_id = os.getenv('FACEBOOK_PAGE_ID')

    if not access_token:
        print("❌ FACEBOOK_ACCESS_TOKEN не найден в .env")
        return

    if not page_id:
        print("❌ FACEBOOK_PAGE_ID не найден в .env")
        return

    print("🔍 Проверка токена Facebook...\n")

    # 1. Проверка типа токена
    print("1️⃣ Проверка типа токена:")
    debug_url = f"https://graph.facebook.com/v18.0/debug_token?input_token={access_token}&access_token={access_token}"

    try:
        response = requests.get(debug_url)
        data = response.json()

        if 'data' in data:
            token_data = data['data']
            print(f"   Тип: {token_data.get('type', 'unknown')}")
            print(f"   Валиден: {token_data.get('is_valid', False)}")
            print(f"   Истекает: {token_data.get('expires_at', 'never')}")

            if token_data.get('type') == 'USER':
                print("\n⚠️  У вас User Token! Нужен Page Token.")
                print("\n📝 Решение:")
                print("   1. Получите Page Token через me/accounts")
                get_page_token(access_token)
                return
        else:
            print(f"   ❌ Ошибка: {data}")
    except Exception as e:
        print(f"   ❌ Ошибка проверки: {e}")

    # 2. Проверка доступа к странице
    print("\n2️⃣ Проверка доступа к странице:")
    page_url = f"https://graph.facebook.com/v18.0/{page_id}?access_token={access_token}"

    try:
        response = requests.get(page_url)
        data = response.json()

        if 'id' in data:
            print(f"   ✅ Страница найдена: {data.get('name')}")
            print(f"   ID: {data.get('id')}")
        else:
            print(f"   ❌ Ошибка доступа: {data.get('error', {}).get('message')}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # 3. Тест публикации
    print("\n3️⃣ Тест публикации:")
    test_post(access_token, page_id)

def get_page_token(user_token):
    """Получить Page Token из User Token"""
    print("\n🔧 Получение Page Token...")

    accounts_url = f"https://graph.facebook.com/v18.0/me/accounts?access_token={user_token}"

    try:
        response = requests.get(accounts_url)
        data = response.json()

        if 'data' in data and len(data['data']) > 0:
            print("\n✅ Найдены страницы:\n")
            for i, page in enumerate(data['data'], 1):
                print(f"{i}. {page['name']}")
                print(f"   ID: {page['id']}")
                print(f"   Access Token: {page['access_token'][:50]}...")
                print(f"   Права: {', '.join(page.get('tasks', []))}")
                print()

                # Показываем как обновить .env
                if i == 1:
                    print("📝 Обновите .env файл:")
                    print(f"FACEBOOK_PAGE_ID={page['id']}")
                    print(f"FACEBOOK_ACCESS_TOKEN={page['access_token']}")
                    print()
        else:
            print("❌ Страницы не найдены или нет доступа")
            print(f"   Ответ: {data}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_post(access_token, page_id):
    """Тестовая публикация"""
    api_url = f"https://graph.facebook.com/v18.0/{page_id}/feed"

    data = {
        'message': '🧪 Test post from Auto Publisher',
        'access_token': access_token
    }

    try:
        response = requests.post(api_url, data=data)
        result = response.json()

        if 'id' in result:
            print(f"   ✅ Тестовый пост опубликован!")
            print(f"   Post ID: {result['id']}")
        else:
            print(f"   ❌ Ошибка публикации:")
            print(f"   {result.get('error', {}).get('message')}")
            print(f"\n   Полный ответ: {result}")

            # Подсказки по ошибкам
            error_msg = result.get('error', {}).get('message', '')
            if 'OAuthException' in error_msg:
                print("\n💡 Решение:")
                print("   - Получите новый Page Token через me/accounts")
                print("   - Убедитесь что токен имеет права pages_manage_posts")
            elif 'permissions' in error_msg.lower():
                print("\n💡 Решение:")
                print("   - Дайте разрешение pages_manage_posts при генерации токена")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    print("="*60)
    print("   ДИАГНОСТИКА FACEBOOK API")
    print("="*60)
    print()

    check_facebook_token()

    print("\n" + "="*60)
    print("\n💡 Рекомендации:")
    print("   1. Если у вас User Token - используйте Page Token из me/accounts")
    print("   2. Получить Page Token: https://developers.facebook.com/tools/explorer/")
    print("   3. Выберите свою страницу и дайте разрешения pages_manage_posts")
    print("\n" + "="*60)
