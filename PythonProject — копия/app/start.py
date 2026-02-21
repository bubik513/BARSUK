from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

# ИСПРАВЛЕННЫЕ ИМПОРТЫ - используем правильные пути
from app.utils.database import create_user, confirm_age_and_save_phone, log_event, UserStatus
from app.utils.keyboards import (
    get_age_keyboard, get_consent_keyboard,
    get_phone_keyboard, get_main_menu_keyboard
)
from app.utils.texts.messages import (
    AGE_CONFIRMATION_TEXT, CONSENT_TEXT,
    MAIN_MENU_TEXT
)

router = Router()


class RegistrationStates(StatesGroup):
    age_confirmation = State()
    consent = State()
    phone = State()


@router.message(Command("start"))
async def start_command(message: Message, db: AsyncSession, state: FSMContext):
    """Начало регистрации"""
    # Создаем/обновляем пользователя
    user = await create_user(
        db=db,
        telegram_user_id=str(message.from_user.id),
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        language_code=message.from_user.language_code
    )

    # Если пользователь уже активен, показываем главное меню
    if user.status == UserStatus.ACTIVE:
        await message.answer(
            MAIN_MENU_TEXT,
            reply_markup=get_main_menu_keyboard()
        )
        return

    # Если не подтвердил возраст, начинаем регистрацию
    await state.set_state(RegistrationStates.age_confirmation)
    await message.answer(
        AGE_CONFIRMATION_TEXT,
        reply_markup=get_age_keyboard(),
        parse_mode="HTML"
    )


@router.message(RegistrationStates.age_confirmation, F.text == "✅ Мне 18+")
async def process_age_confirmation(message: Message, db: AsyncSession, state: FSMContext):
    """Пользователь подтвердил 18+"""
    await log_event(db, message.from_user.id, "age_confirmed")
    await state.set_state(RegistrationStates.consent)
    await message.answer(
        CONSENT_TEXT,
        reply_markup=get_consent_keyboard(),
        parse_mode="HTML"
    )


@router.message(RegistrationStates.age_confirmation, F.text == "❌ Нет, мне еще нет 18")
async def process_age_rejection(message: Message, db: AsyncSession, state: FSMContext):
    """Пользователю нет 18 лет"""
    await log_event(db, message.from_user.id, "age_failed")
    await message.answer(
        "❌ Доступ к боту запрещен. Только для лиц старше 18 лет.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()


@router.message(RegistrationStates.consent, F.text == "✅ Я согласен на обработку данных")
async def process_consent(message: Message, db: AsyncSession, state: FSMContext):
    """Пользователь согласился на обработку данных"""
    await log_event(db, message.from_user.id, "consent_accepted")
    await state.set_state(RegistrationStates.phone)
    await message.answer(
        "✅ Спасибо! Теперь нам нужен ваш номер телефона для связи.",
        reply_markup=get_phone_keyboard()
    )


@router.message(RegistrationStates.consent, F.text == "❌ Отказаться")
async def process_consent_rejection(message: Message, state: FSMContext):
    """Пользователь отказался от согласия"""
    await message.answer(
        "❌ Для использования бота необходимо согласие на обработку данных.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()


@router.message(RegistrationStates.phone, F.contact)
async def process_phone(message: Message, db: AsyncSession, state: FSMContext):
    """Получение и сохранение телефона"""
    phone = message.contact.phone_number

    # Сохраняем данные
    user = await confirm_age_and_save_phone(
        db=db,
        telegram_user_id=str(message.from_user.id),
        phone=phone,
        consent_version="1.0"
    )

    if user:
        await message.answer(
            f"✅ Регистрация завершена!\n\n"
            f"Телефон: {phone}\n\n"
            f"{MAIN_MENU_TEXT}",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Ошибка при сохранении данных. Попробуйте снова /start",
            reply_markup=ReplyKeyboardRemove()
        )

    await state.clear()


def register_start_handlers(dp):
    dp.include_router(router)