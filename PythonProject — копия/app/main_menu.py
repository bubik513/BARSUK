from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.utils.database import log_event, User, UserStatus, ContentCategory, ContentItem
from app.utils.keyboards import get_main_menu_keyboard
from app.utils.texts.messages import RULES_TEXT
from app.utils.content import get_categories, get_category_items, format_category_text

router = Router()

# Мидлварь для проверки доступа
async def check_access(message: Message, db: AsyncSession):
    """Проверяет, есть ли у пользователя доступ к функциям"""
    user_id = message.from_user.id

    stmt = select(User).where(User.telegram_id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or user.status != UserStatus.ACTIVE:
        await message.answer(
            "❌ Доступ запрещен. Пройдите регистрацию через /start"
        )
        return False
    return True


# Главное меню - ПОКАЗ КАТЕГОРИЙ
@router.message(F.text == "📌 Меню / Программы")
async def menu_programs(message: Message, db: AsyncSession):
    """
    Показ категорий меню из базы данных
    """
    if not await check_access(message, db):
        return

    await log_event(db, message.from_user.id, "menu_opened")

    # Получаем категории из БД
    categories = await get_categories(db)

    if not categories:
        await message.answer(
            "🍷 Меню временно не доступно. Скоро обновим!",
            reply_markup=get_main_menu_keyboard()
        )
        return

    # Создаем инлайн клавиатуру с категориями
    keyboard_buttons = []
    for cat in categories:
        keyboard_buttons.append([InlineKeyboardButton(
            text=cat.name,
            callback_data=f"category_{cat.id}"
        )])

    await message.answer(
        "🍷 <b>Наше меню:</b>\n\nВыберите категорию:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
        parse_mode="HTML"
    )


# ПОКАЗ ПОЗИЦИЙ ВЫБРАННОЙ КАТЕГОРИИ
@router.callback_query(F.data.startswith("category_"))
async def show_category(callback: CallbackQuery, db: AsyncSession):
    """Показ позиций выбранной категории"""
    category_id = int(callback.data.split("_")[1])

    # Получаем категорию
    from sqlalchemy import select
    from app.utils.database import ContentCategory

    stmt = select(ContentCategory).where(ContentCategory.id == category_id)
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()

    if not category:
        await callback.answer("Категория не найдена")
        return

    # Получаем позиции категории
    items = await get_category_items(db, category_id)

    if not items:
        await callback.message.edit_text(
            f"<b>{category.name}</b>\n\nВ этой категории пока нет позиций",
            parse_mode="HTML"
        )
        return

    # Форматируем текст с позициями
    text = f"<b>{category.name}</b>\n\n"

    for item in items:
        text += f"• <b>{item.name}</b>\n"
        if item.description:
            text += f"  {item.description}\n"
        text += f"  {item.price_display}\n\n"

    # Кнопка "Назад к категориям"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к меню", callback_data="back_to_menu")]
    ])

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


# ВОЗВРАТ К СПИСКУ КАТЕГОРИЙ
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, db: AsyncSession):
    """Возврат к списку категорий"""
    # Получаем категории из БД
    categories = await get_categories(db)

    if not categories:
        await callback.message.edit_text(
            "🍷 Меню временно не доступно.",
            parse_mode="HTML"
        )
        return

    # Создаем клавиатуру с категориями
    keyboard_buttons = []
    for cat in categories:
        keyboard_buttons.append([InlineKeyboardButton(
            text=cat.name,
            callback_data=f"category_{cat.id}"
        )])

    await callback.message.edit_text(
        "🍷 <b>Наше меню:</b>\n\nВыберите категорию:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
        parse_mode="HTML"
    )
    await callback.answer()


# Правила и FAQ
@router.message(F.text == "ℹ️ Правила / FAQ")
async def send_rules(message: Message, db: AsyncSession):
    """
    Отправка правил клуба
    """
    if not await check_access(message, db):
        return

    await log_event(db, message.from_user.id, "rules_opened")
    await message.answer(
        RULES_TEXT,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )


# Заглушки для будущих функций
@router.message(F.text == "⭐ Мой статус")
async def my_status(message: Message, db: AsyncSession):
    if not await check_access(message, db):
        return

    await message.answer(
        "⭐ <b>Система лояльности</b>\n\n"
        "Функция будет доступна в следующем обновлении.\n"
        "Следите за анонсами!",
        parse_mode="HTML"
    )


@router.message(F.text == "🎁 Промокоды")
async def promocodes(message: Message, db: AsyncSession):
    if not await check_access(message, db):
        return

    await message.answer(
        "🎁 <b>Промокоды и акции</b>\n\n"
        "Функция будет доступна в следующем обновлении.\n"
        "Следите за рассылками!",
        parse_mode="HTML"
    )


def register_main_menu_handlers(dp):
    dp.include_router(router)