from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Request
from .admin_actions import send_telegram_message
import json


@staff_member_required
def reply_to_request_view(request, request_id):
    """View для ответа на заявку"""
    print("\n" + "=" * 50)
    print(f"🔍 ВХОД В VIEW для заявки #{request_id}")
    print(f"Метод запроса: {request.method}")

    request_obj = get_object_or_404(Request, id=request_id)

    print(f"Заявка: #{request_obj.id}")
    print(f"Тип: {request_obj.request_type}")
    print(f"Пользователь: {request_obj.user}")
    print(f"Telegram ID: {request_obj.user.telegram_id}")

    if request.method == 'POST':
        print("\n📨 ПОЛУЧЕН POST ЗАПРОС")
        reply_text = request.POST.get('reply', '').strip()
        print(f"Текст ответа: {reply_text[:50]}...")

        if reply_text:
            # Отправляем ответ пользователю
            user = request_obj.user
            print(f"Telegram ID пользователя: {user.telegram_id}")

            if user and user.telegram_id:
                message = f"📬 <b>Ответ на вашу заявку #{request_obj.id}</b>\n\n{reply_text}"
                print(f"Формируем сообщение: {message[:50]}...")

                print("🚀 Вызываем send_telegram_message...")
                result = send_telegram_message(user.telegram_id, message)
                print(f"Результат отправки: {result}")

                if result:
                    print("✅ Отправка успешна!")
                    # Сохраняем ответ в заметках
                    notes = f"Ответ менеджера ({request.user.username}):\n{reply_text}\n\n[reply_sent]"
                    request_obj.manager_notes = notes
                    request_obj.status = 'done'
                    request_obj.save()

                    messages.success(request, f'✅ Ответ отправлен пользователю!')
                    print("✅ Перенаправление на список заявок")
                    return redirect('admin:barsuk_app_request_changelist')
                else:
                    print("❌ Ошибка при отправке сообщения")
                    messages.error(request, '❌ Ошибка при отправке сообщения в Telegram')
            else:
                print("❌ У пользователя нет Telegram ID")
                messages.error(request, '❌ У пользователя нет Telegram ID')
        else:
            print("❌ Введите текст ответа")
            messages.error(request, '❌ Введите текст ответа')

    print("=" * 50 + "\n")

    return render(request, 'admin/reply_to_request.html', {
        'request_obj': request_obj,
        'title': f'Ответ на заявку #{request_obj.id}'
    })