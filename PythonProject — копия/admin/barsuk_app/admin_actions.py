from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
import requests
import json


def send_telegram_message(telegram_id, text):
    """Отправка сообщения пользователю через бота"""
    print(f"\n📤 ФУНКЦИЯ send_telegram_message:")
    print(f"   Telegram ID: {telegram_id}")
    print(f"   Текст: {text[:50]}...")

    try:
        # Токен вашего бота
        BOT_TOKEN = "8557869481:AAGM6AJ86Os6lbV_3Csydcrgo8hZpqtldtk"
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        data = {
            "chat_id": telegram_id,
            "text": text,
            "parse_mode": "HTML"
        }

        print(f"   URL: {url}")
        print(f"   Данные: {json.dumps(data, ensure_ascii=False)}")

        print("   Отправка запроса...")
        response = requests.post(url, json=data, timeout=10)

        print(f"   Статус ответа: {response.status_code}")
        print(f"   Тело ответа: {response.text}")

        # Проверяем ответ
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("   ✅ Успешно!")
                return True
            else:
                print(f"   ❌ Ошибка API: {result}")
                return False
        else:
            print(f"   ❌ HTTP ошибка: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print("   ❌ Таймаут")
        return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Ошибка соединения")
        return False
    except Exception as e:
        print(f"   ❌ Исключение: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


# Кастомное действие для админки - ЭТА ФУНКЦИЯ ДОЛЖНА БЫТЬ!
def reply_to_request(modeladmin, request, queryset):
    """Действие для ответа на выбранные заявки"""
    # Берем первую выбранную заявку
    selected = queryset.first()
    if selected:
        # Перенаправляем на страницу ответа
        return HttpResponseRedirect(
            reverse('reply_to_request', args=[selected.id])
        )
    else:
        messages.warning(request, "Выберите одну заявку для ответа")


reply_to_request.short_description = "📝 Ответить на заявку"