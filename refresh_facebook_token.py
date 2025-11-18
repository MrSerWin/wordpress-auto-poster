#!/usr/bin/env python3
"""
Автоматическое обновление Facebook Page Token
Использует App ID и App Secret для обмена токена на long-lived версию
"""
import os
import sys
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


def refresh_facebook_token():
    """Обновляет Facebook Page Token на long-lived версию (60 дней)"""

    print("="*60)
    print("   ОБНОВЛЕНИЕ FACEBOOK PAGE TOKEN")
    print("="*60)
    print()

    # Получение credentials из .env
    app_id = os.getenv('FACEBOOK_APP_ID')
    app_secret = os.getenv('FACEBOOK_APP_SECRET')
    current_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
    page_id = os.getenv('FACEBOOK_PAGE_ID')

    # Проверка наличия всех необходимых данных
    missing = []
    if not app_id:
        missing.append('FACEBOOK_APP_ID')
    if not app_secret:
        missing.append('FACEBOOK_APP_SECRET')
    if not current_token:
        missing.append('FACEBOOK_ACCESS_TOKEN')
    if not page_id:
        missing.append('FACEBOOK_PAGE_ID')

    if missing:
        print("❌ Отсутствуют необходимые credentials в .env файле:")
        for var in missing:
            print(f"   - {var}")
        print()
        print("Добавьте в .env файл:")
        print("FACEBOOK_APP_ID=your_app_id")
        print("FACEBOOK_APP_SECRET=your_app_secret")
        print("FACEBOOK_PAGE_ID=your_page_id")
        print("FACEBOOK_ACCESS_TOKEN=your_current_token")
        print()
        print("Получить App ID и App Secret:")
        print("  https://developers.facebook.com/apps")
        return False

    print(f"✅ Credentials найдены")
    print(f"   App ID: {app_id}")
    print(f"   Page ID: {page_id}")
    print()

    try:
        # Шаг 1: Проверка текущего токена
        print("🔍 Проверка текущего токена...")
        debug_url = f"https://graph.facebook.com/v18.0/debug_token"
        params = {
            'input_token': current_token,
            'access_token': current_token
        }

        response = requests.get(debug_url, params=params)
        if response.status_code == 200:
            data = response.json().get('data', {})
            token_type = data.get('type')
            is_valid = data.get('is_valid')
            expires_at = data.get('expires_at')

            print(f"   Тип токена: {token_type}")
            print(f"   Валидный: {is_valid}")

            if expires_at == 0:
                print(f"   Срок действия: Бессрочный ♾️")
                print()
                print("✅ У вас уже бессрочный токен!")
                print("   Обновление не требуется.")
                return True
            else:
                from datetime import datetime
                exp_date = datetime.fromtimestamp(expires_at)
                print(f"   Истекает: {exp_date}")
        print()

        # Шаг 2: Обмен на long-lived User Token
        print("🔄 Шаг 1/3: Обмен на long-lived User Token...")
        exchange_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': app_id,
            'client_secret': app_secret,
            'fb_exchange_token': current_token
        }

        response = requests.get(exchange_url, params=params)
        response.raise_for_status()

        token_data = response.json()
        long_lived_user_token = token_data.get('access_token')
        expires_in = token_data.get('expires_in', 0)

        print(f"   ✅ Получен long-lived User Token")
        if expires_in:
            print(f"   Срок действия: {expires_in // 86400} дней")
        print()

        # Шаг 3: Получить Page Token из User Token
        print("🔄 Шаг 2/3: Получение Page Access Token...")
        accounts_url = f"https://graph.facebook.com/v18.0/me/accounts"
        params = {'access_token': long_lived_user_token}

        response = requests.get(accounts_url, params=params)
        response.raise_for_status()

        pages = response.json().get('data', [])

        if not pages:
            print("❌ Страницы не найдены")
            print("   Убедитесь что токен имеет права pages_show_list")
            return False

        print(f"   Найдено страниц: {len(pages)}")

        # Найти нужную страницу
        page_token = None
        page_name = None
        for page in pages:
            if page['id'] == page_id:
                page_token = page['access_token']
                page_name = page['name']
                break

        if not page_token:
            print(f"❌ Страница с ID {page_id} не найдена")
            print()
            print("Доступные страницы:")
            for page in pages:
                print(f"   - {page['name']} (ID: {page['id']})")
            return False

        print(f"   ✅ Получен Page Token для: {page_name}")
        print()

        # Шаг 4: Проверка нового токена
        print("🔍 Шаг 3/3: Проверка нового токена...")
        debug_url = f"https://graph.facebook.com/v18.0/debug_token"
        params = {
            'input_token': page_token,
            'access_token': page_token
        }

        response = requests.get(debug_url, params=params)
        if response.status_code == 200:
            data = response.json().get('data', {})
            expires_at = data.get('expires_at')

            if expires_at == 0:
                print(f"   ✅ Токен бессрочный ♾️")
            else:
                from datetime import datetime
                exp_date = datetime.fromtimestamp(expires_at)
                days_valid = (exp_date - datetime.now()).days
                print(f"   Истекает: {exp_date}")
                print(f"   Действителен: ~{days_valid} дней")
        print()

        # Шаг 5: Обновить .env файл
        print("💾 Обновление .env файла...")

        env_file = Path('.env')
        if not env_file.exists():
            print("❌ .env файл не найден")
            return False

        # Читаем содержимое
        with open(env_file, 'r') as f:
            lines = f.readlines()

        # Обновляем токен
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('FACEBOOK_ACCESS_TOKEN='):
                lines[i] = f'FACEBOOK_ACCESS_TOKEN={page_token}\n'
                updated = True
                break

        if not updated:
            print("⚠️ FACEBOOK_ACCESS_TOKEN не найден в .env, добавляю...")
            lines.append(f'FACEBOOK_ACCESS_TOKEN={page_token}\n')

        # Записываем обратно
        with open(env_file, 'w') as f:
            f.writelines(lines)

        print(f"   ✅ Токен обновлен в .env файле")
        print()

        # Итоговый отчет
        print("="*60)
        print("🎉 ТОКЕН УСПЕШНО ОБНОВЛЕН!")
        print("="*60)
        print()
        print(f"Страница: {page_name}")
        print(f"Page ID: {page_id}")
        print(f"Новый токен сохранен в .env")
        print()
        print("Следующее обновление:")
        if expires_at == 0:
            print("  Не требуется (бессрочный токен)")
        else:
            print(f"  Через ~{days_valid} дней")
            print(f"  Рекомендуется запустить за неделю до истечения")
        print()
        print("Автоматизация (cron):")
        print("  0 3 */50 * * cd /path/to/project && python refresh_facebook_token.py")
        print()

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP ошибка: {e}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Ошибка обновления токена: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_token_expiry():
    """Проверяет когда истекает текущий токен"""

    load_dotenv()
    current_token = os.getenv('FACEBOOK_ACCESS_TOKEN')

    if not current_token:
        print("❌ FACEBOOK_ACCESS_TOKEN не найден в .env")
        return

    try:
        debug_url = f"https://graph.facebook.com/v18.0/debug_token"
        params = {
            'input_token': current_token,
            'access_token': current_token
        }

        response = requests.get(debug_url, params=params)
        response.raise_for_status()

        data = response.json().get('data', {})
        expires_at = data.get('expires_at')
        is_valid = data.get('is_valid')
        token_type = data.get('type')

        print("="*60)
        print("   ПРОВЕРКА FACEBOOK TOKEN")
        print("="*60)
        print()
        print(f"Тип токена: {token_type}")
        print(f"Валидный: {'✅ Да' if is_valid else '❌ Нет'}")

        if expires_at == 0:
            print(f"Срок действия: ✅ Бессрочный ♾️")
            print()
            print("Токен не требует обновления!")
        else:
            from datetime import datetime
            exp_date = datetime.fromtimestamp(expires_at)
            days_left = (exp_date - datetime.now()).days

            print(f"Истекает: {exp_date}")
            print(f"Осталось: {days_left} дней")
            print()

            if days_left < 7:
                print("⚠️ ВНИМАНИЕ: Токен скоро истечет!")
                print("   Запустите: python refresh_facebook_token.py")
            elif days_left < 30:
                print("⚠️ Рекомендуется обновить токен в ближайшее время")
            else:
                print("✅ Токен действителен")

        print()
        print("="*60)

    except Exception as e:
        print(f"❌ Ошибка проверки токена: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Facebook Token Manager')
    parser.add_argument('--check', action='store_true',
                       help='Только проверить срок действия токена')
    parser.add_argument('--refresh', action='store_true',
                       help='Обновить токен на long-lived версию')

    args = parser.parse_args()

    if args.check:
        check_token_expiry()
    elif args.refresh:
        success = refresh_facebook_token()
        sys.exit(0 if success else 1)
    else:
        # По умолчанию - обновление
        print("Используйте:")
        print("  --check   : Проверить срок действия токена")
        print("  --refresh : Обновить токен")
        print()
        print("Запуск проверки...")
        print()
        check_token_expiry()
