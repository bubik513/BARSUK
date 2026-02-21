from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

# ИСПРАВЛЕННЫЕ ИМПОРТЫ
from app.utils.database import Request, User, log_event
from app.utils.keyboards import (
    get_main_menu_keyboard, get_cancel_keyboard,
    get_confirm_keyboard, get_edit_fields_keyboard
)

router = Router()


# ====== СОСТОЯНИЯ ДЛЯ FSM ======

class TransferRequestStates(StatesGroup):
    """Состояния для заявки на трансфер"""
    address = State()
    date = State()
    time = State()
    guests = State()
    comment = State()
    confirm = State()
    edit = State()


class ManagerRequestStates(StatesGroup):
    """Состояния для заявки менеджеру"""
    message = State()
    confirm = State()


# ====== ОБЩИЕ ФУНКЦИИ ======

async def cancel_request(message: Message, state: FSMContext):
    """Отмена заявки и возврат в главное меню"""
    await message.answer(
        "❌ Заявка отменена.",
        reply_markup=get_main_menu_keyboard()
    )
    await state.clear()


async def get_user_info(db: AsyncSession, user_id: int) -> dict:
    """Получение информации о пользователе"""
    stmt = select(User).where(User.telegram_id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        return {
            "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
            "phone": user.phone or "Не указан",
            "username": f"@{user.username}" if user.username else "Нет username"
        }
    return {"name": "Неизвестно", "phone": "Не указан", "username": "Нет username"}


# ====== ТРАНСФЕР (ПОЛНАЯ ФОРМА) ======

@router.message(F.text == "🚖 Заказать трансфер")
async def start_transfer_request(message: Message, db: AsyncSession, state: FSMContext):
    """Начало оформления заявки на трансфер"""
    await log_event(db, message.from_user.id, "transfer_requested")

    await state.set_state(TransferRequestStates.address)
    await message.answer(
        "🚖 <b>Заказ трансфера</b>\n\n"
        "Заполните форму для заказа трансфера:\n\n"
        "1. <b>Введите адрес подачи:</b>\n"
        "(улица, дом, подъезд - чем подробнее, тем лучше)",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(TransferRequestStates.address)
async def process_transfer_address(message: Message, state: FSMContext):
    """Обработка адреса"""
    if message.text == "❌ Отмена":
        await cancel_request(message, state)
        return

    if len(message.text.strip()) < 5:
        await message.answer("❌ Адрес слишком короткий. Введите полный адрес:")
        return

    await state.update_data(address=message.text.strip())
    await state.set_state(TransferRequestStates.date)
    await message.answer(
        "2. <b>Выберите дату:</b>\n"
        "Напишите 'сегодня', 'завтра' или конкретную дату (ДД.ММ):",
        parse_mode="HTML"
    )


@router.message(TransferRequestStates.date)
async def process_transfer_date(message: Message, state: FSMContext):
    """Обработка даты"""
    if message.text == "❌ Отмена":
        await cancel_request(message, state)
        return

    date_text = message.text.strip().lower()
    valid_options = ["сегодня", "завтра"]

    if date_text not in valid_options and not _validate_date(date_text):
        await message.answer(
            "❌ Некорректная дата. Используйте:\n"
            "- 'сегодня'\n"
            "- 'завтра'\n"
            "- дату в формате ДД.ММ (например, 15.02)"
        )
        return

    await state.update_data(date=date_text)
    await state.set_state(TransferRequestStates.time)
    await message.answer(
        "3. <b>Введите время:</b>\n"
        "Формат: ЧЧ:ММ (например, 22:30 или 19:00)",
        parse_mode="HTML"
    )


@router.message(TransferRequestStates.time)
async def process_transfer_time(message: Message, state: FSMContext):
    """Обработка времени"""
    if message.text == "❌ Отмена":
        await cancel_request(message, state)
        return

    time_text = message.text.strip()
    if not _validate_time(time_text):
        await message.answer(
            "❌ Некорректное время. Используйте формат ЧЧ:ММ\n"
            "Например: 22:30, 19:00, 02:15"
        )
        return

    await state.update_data(time=time_text)
    await state.set_state(TransferRequestStates.guests)
    await message.answer(
        "4. <b>Количество гостей:</b>\n"
        "Введите число от 1 до 10:",
        parse_mode="HTML"
    )


@router.message(TransferRequestStates.guests)
async def process_transfer_guests(message: Message, state: FSMContext):
    """Обработка количества гостей"""
    if message.text == "❌ Отмена":
        await cancel_request(message, state)
        return

    try:
        guests = int(message.text.strip())
        if guests < 1 or guests > 10:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите число от 1 до 10:")
        return

    await state.update_data(guests=guests)
    await state.set_state(TransferRequestStates.comment)
    await message.answer(
        "5. <b>Комментарий (необязательно):</b>\n"
        "Укажите дополнительные пожелания или оставьте пустым:",
        parse_mode="HTML"
    )


@router.message(TransferRequestStates.comment)
async def process_transfer_comment(message: Message, state: FSMContext):
    """Обработка комментария"""
    if message.text == "❌ Отмена":
        await cancel_request(message, state)
        return

    comment = message.text.strip() if message.text.strip() != "❌ Отмена" else ""
    await state.update_data(comment=comment)

    # Показываем сводку
    await show_transfer_summary(message, state)


async def show_transfer_summary(message: Message, state: FSMContext):
    """Показать сводку заявки на трансфер"""
    data = await state.get_data()

    summary = (
        "📋 <b>Проверьте информацию:</b>\n\n"
        f"📍 <b>Адрес:</b> {data.get('address', 'Не указан')}\n"
        f"📅 <b>Дата:</b> {data.get('date', 'Не указана')}\n"
        f"🕐 <b>Время:</b> {data.get('time', 'Не указано')}\n"
        f"👥 <b>Гостей:</b> {data.get('guests', 'Не указано')}\n"
    )

    if data.get('comment'):
        summary += f"💬 <b>Комментарий:</b> {data['comment']}\n"

    summary += "\n✅ Всё верно?"

    await state.set_state(TransferRequestStates.confirm)
    await message.answer(
        summary,
        reply_markup=get_confirm_keyboard(),
        parse_mode="HTML"
    )


@router.message(TransferRequestStates.confirm)
async def process_transfer_confirm(message: Message, db: AsyncSession, state: FSMContext):
    """Подтверждение заявки на трансфер"""
    if message.text == "❌ Отмена":
        await cancel_request(message, state)
        return

    if message.text == "✏️ Редактировать":
        await state.set_state(TransferRequestStates.edit)
        await message.answer(
            "✏️ <b>Что хотите изменить?</b>",
            reply_markup=get_edit_fields_keyboard(),
            parse_mode="HTML"
        )
        return

    if message.text == "✅ Да, отправить":
        data = await state.get_data()
        user_info = await get_user_info(db, message.from_user.id)

        # ===== ИСПРАВЛЕНИЕ: сначала находим пользователя по telegram_id =====
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(
                "❌ Ошибка: пользователь не найден. Попробуйте перезапустить бота /start",
                reply_markup=get_main_menu_keyboard()
            )
            await state.clear()
            return

        # Сохраняем заявку в базу с правильным user.id
        request = Request(
            user_id=user.id,  # ВАЖНО: используем внутренний ID, а не telegram_id
            request_type="transfer",
            data={
                "address": data.get('address'),
                "date": data.get('date'),
                "time": data.get('time'),
                "guests": data.get('guests'),
                "comment": data.get('comment', ''),
                "user_info": user_info
            },
            status="new",
            created_at=datetime.utcnow()
        )

        db.add(request)
        await db.commit()

        await log_event(db, message.from_user.id, "transfer_request_submitted", {
            "request_id": request.id,
            "address": data.get('address'),
            "guests": data.get('guests')
        })

        # Уведомление пользователю
        await message.answer(
            f"✅ <b>Заявка №{request.id} отправлена!</b>\n\n"
            "📞 Менеджер свяжется с вами для подтверждения.\n"
            "⏱️ Обычно это занимает 10-15 минут.\n\n"
            "<i>Номер заявки сохраните для уточнений.</i>",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )

        # Отправляем уведомление менеджеру
        await notify_manager_about_request(request, user_info)

        await state.clear()
        return


@router.message(TransferRequestStates.edit)
async def process_transfer_edit(message: Message, state: FSMContext):
    """Редактирование полей заявки"""
    if message.text == "❌ Отмена":
        await cancel_request(message, state)
        return

    if message.text == "✅ Всё верно, отправить":
        await state.set_state(TransferRequestStates.confirm)
        await show_transfer_summary(message, state)
        return

    field_map = {
        "📍 Адрес": ("address", TransferRequestStates.address, "Введите новый адрес:"),
        "🕐 Время": ("time", TransferRequestStates.time, "Введите новое время (ЧЧ:ММ):"),
        "👥 Гостей": ("guests", TransferRequestStates.guests, "Введите новое количество гостей:"),
        "💬 Комментарий": ("comment", TransferRequestStates.comment, "Введите новый комментарий:")
    }

    if message.text in field_map:
        field_name, next_state, prompt = field_map[message.text]

        # Если редактируем дату, нужно особое поведение
        if message.text == "📅 Дата":
            await state.set_state(TransferRequestStates.date)
            await message.answer(
                "Введите новую дату ('сегодня', 'завтра' или ДД.ММ):",
                reply_markup=get_cancel_keyboard()
            )
            return

        await state.set_state(next_state)
        await message.answer(
            prompt,
            reply_markup=get_cancel_keyboard()
        )
    else:
        await message.answer("Выберите поле для редактирования:", reply_markup=get_edit_fields_keyboard())


# ====== МЕНЕДЖЕР (ПОЛНАЯ ФОРМА) ======

@router.message(F.text == "💬 Связаться с менеджером")
async def start_manager_request(message: Message, db: AsyncSession, state: FSMContext):
    """Начало заявки на связь с менеджером"""
    await log_event(db, message.from_user.id, "manager_contact_clicked")

    await state.set_state(ManagerRequestStates.message)
    await message.answer(
        "💬 <b>Связь с менеджером</b>\n\n"
        "Опишите ваш вопрос или тему для обсуждения:\n"
        "(чем подробнее, тем быстрее мы сможем помочь)",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(ManagerRequestStates.message)
async def process_manager_message(message: Message, state: FSMContext):
    """Обработка сообщения менеджеру"""
    if message.text == "❌ Отмена":
        await cancel_request(message, state)
        return

    if len(message.text.strip()) < 5:
        await message.answer("❌ Сообщение слишком короткое. Опишите вопрос подробнее:")
        return

    await state.update_data(message=message.text.strip())

    # Показываем сводку
    await show_manager_summary(message, state)


async def show_manager_summary(message: Message, state: FSMContext):
    """Показать сводку заявки менеджеру"""
    data = await state.get_data()

    summary = (
        "📋 <b>Ваше сообщение:</b>\n\n"
        f"{data.get('message', '')}\n\n"
        "✅ Отправить менеджеру?"
    )

    await state.set_state(ManagerRequestStates.confirm)
    await message.answer(
        summary,
        reply_markup=get_confirm_keyboard(),
        parse_mode="HTML"
    )


@router.message(ManagerRequestStates.confirm)
async def process_manager_confirm(message: Message, db: AsyncSession, state: FSMContext):
    """Подтверждение заявки менеджеру"""
    if message.text == "❌ Отмена":
        await cancel_request(message, state)
        return

    if message.text == "✏️ Редактировать":
        await state.set_state(ManagerRequestStates.message)
        await message.answer(
            "✏️ <b>Отредактируйте ваше сообщение:</b>",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    if message.text == "✅ Да, отправить":
        data = await state.get_data()
        user_info = await get_user_info(db, message.from_user.id)

        # ===== ИСПРАВЛЕНИЕ: сначала находим пользователя по telegram_id =====
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(
                "❌ Ошибка: пользователь не найден. Попробуйте перезапустить бота /start",
                reply_markup=get_main_menu_keyboard()
            )
            await state.clear()
            return

        # Сохраняем заявку в базу с правильным user.id
        request = Request(
            user_id=user.id,  # ВАЖНО: используем внутренний ID, а не telegram_id
            request_type="manager",
            data={
                "message": data.get('message'),
                "user_info": user_info
            },
            status="new",
            created_at=datetime.utcnow()
        )

        db.add(request)
        await db.commit()

        await log_event(db, message.from_user.id, "manager_request_submitted", {
            "request_id": request.id,
            "message_length": len(data.get('message', ''))
        })

        # Уведомление пользователю
        await message.answer(
            f"✅ <b>Заявка №{request.id} отправлена!</b>\n\n"
            "📞 Менеджер свяжется с вами в ближайшее время.\n"
            "⏱️ Среднее время ответа: 15-30 минут.\n\n"
            "<i>Номер заявки сохраните для уточнений.</i>",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )

        # Отправляем уведомление менеджеру
        await notify_manager_about_request(request, user_info)

        await state.clear()
        return


# ====== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======

def _validate_date(date_text: str) -> bool:
    """Валидация даты"""
    try:
        if '.' in date_text:
            day, month = map(int, date_text.split('.'))
            return 1 <= day <= 31 and 1 <= month <= 12
        return date_text in ["сегодня", "завтра"]
    except:
        return False


def _validate_time(time_text: str) -> bool:
    """Валидация времени"""
    try:
        if ':' not in time_text:
            return False
        hour, minute = map(int, time_text.split(':'))
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except:
        return False


async def notify_manager_about_request(request: Request, user_info: dict):
    """
    Уведомление менеджера о новой заявке
    Пока заглушка - потом реализуем через Telegram бота или веб-хук
    """
    print(f"\n🔔 НОВАЯ ЗАЯВКА #{request.id}")
    print(f"Тип: {request.request_type}")
    print(f"Пользователь: {user_info['name']}")
    print(f"Телефон: {user_info['phone']}")
    print(f"Username: {user_info['username']}")
    print(f"Время: {request.created_at}")
    print("-" * 40)


def register_requests_handlers(dp):
    dp.include_router(router)