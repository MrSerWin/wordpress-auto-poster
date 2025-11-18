#!/usr/bin/env python3
"""
Простой скрипт для получения Facebook Page Token
Не требует .env файла - просто запустите и следуйте инструкциям
"""
import sys
import requests

def main():
    print("="*60)
    print("   ПОЛУЧЕНИЕ FACEBOOK PAGE TOKEN")
    print("="*60)
    print()
    print("Шаги:")
    print("1. Откройте: https://developers.facebook.com/tools/explorer/")
    print("2. Добавьте права (Permissions):")
    print("   - pages_show_list")
    print("   - pages_manage_posts")
    print("   - pages_read_engagement")
    print("3. Нажмите 'Generate Access Token'")
    print("4. Скопируйте токен и вставьте ниже")
    print()

    # Получить User Token от пользователя
    user_token = input("Вставьте User Access Token: ").strip()

    if not user_token:
        print("\n❌ Токен не введен")
        sys.exit(1)

    print()
    print("🔄 Получение списка ваших Facebook Pages...")

    try:
        # Получаем список страниц
        accounts_url = "https://graph.facebook.com/v18.0/me/accounts"
        params = {'access_token': user_token}

        response = requests.get(accounts_url, params=params, timeout=10)
        response.raise_for_status()

        pages = response.json().get('data', [])

        if not pages:
            print("\n❌ Страницы не найдены")
            print("   Проверьте что:")
            print("   1. Вы добавили permission 'pages_show_list'")
            print("   2. У вас есть Facebook Pages где вы админ")
            sys.exit(1)

        print(f"\n✅ Найдено страниц: {len(pages)}")
        print()
        print("Ваши страницы:")
        for i, page in enumerate(pages, 1):
            print(f"{i}. {page['name']}")
            print(f"   ID: {page['id']}")
            print(f"   Права: {', '.join(page.get('tasks', []))}")

        print()

        # Найти нужную страницу (The Next AI)
        target_page_id = "632284956645073"
        page_token = None
        page_name = None

        for page in pages:
            if page['id'] == target_page_id:
                page_token = page['access_token']
                page_name = page['name']
                break

        if not page_token:
            print(f"⚠️  Страница с ID {target_page_id} не найдена")
            print()

            # Предложить выбрать из списка
            if pages:
                print("Выберите страницу из списка выше:")
                choice = input(f"Введите номер (1-{len(pages)}): ").strip()

                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(pages):
                        selected_page = pages[idx]
                        page_token = selected_page['access_token']
                        page_name = selected_page['name']
                        target_page_id = selected_page['id']
                    else:
                        print("❌ Неверный номер")
                        sys.exit(1)
                except ValueError:
                    print("❌ Введите число")
                    sys.exit(1)

        print()
        print("="*60)
        print(f"✅ ПОЛУЧЕН PAGE TOKEN")
        print("="*60)
        print(f"Страница: {page_name}")
        print(f"Page ID: {target_page_id}")
        print()

        # Проверка токена
        print("🔍 Проверка токена...")
        debug_url = "https://graph.facebook.com/v18.0/debug_token"
        params = {
            'input_token': page_token,
            'access_token': page_token
        }

        response = requests.get(debug_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json().get('data', {})
            token_type = data.get('type')
            is_valid = data.get('is_valid')
            expires_at = data.get('expires_at')

            print(f"   Тип: {token_type}")
            print(f"   Валидный: {'✅ Да' if is_valid else '❌ Нет'}")

            if expires_at == 0:
                print(f"   Срок: ✅ Бессрочный ♾️")
            else:
                from datetime import datetime
                exp_date = datetime.fromtimestamp(expires_at)
                days = (exp_date - datetime.now()).days
                print(f"   Истекает: {exp_date}")
                print(f"   Осталось: ~{days} дней")

        print()
        print("="*60)
        print("ДОБАВЬТЕ В .env ФАЙЛ:")
        print("="*60)
        print()
        print(f"FACEBOOK_PAGE_ID={target_page_id}")
        print(f"FACEBOOK_ACCESS_TOKEN={page_token}")
        print()
        print("="*60)
        print()
        print("Скопируйте токен выше и вставьте в .env файл")
        print()

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Ошибка: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_msg = error_data.get('error', {}).get('message', '')
                if error_msg:
                    print(f"   Сообщение: {error_msg}")
            except:
                pass
        print("\nВозможные причины:")
        print("  1. Токен истек - получите новый")
        print("  2. Не добавлены права (permissions)")
        print("  3. Неправильный токен")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Отменено пользователем")
        sys.exit(1)
