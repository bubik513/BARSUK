from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Клавиатура подтверждения 18+
def get_age_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Мне 18+")],
            [KeyboardButton(text="❌ Нет, мне еще нет 18")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Клавиатура согласия
def get_consent_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Я согласен на обработку данных")],
            [KeyboardButton(text="❌ Отказаться")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Клавиатура запроса телефона
def get_phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Главное меню
def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📌 Меню / Программы")],
            [KeyboardButton(text="🚖 Заказать трансфер"),
             KeyboardButton(text="💬 Связаться с менеджером")],
            [KeyboardButton(text="⭐ Мой статус"),
             KeyboardButton(text="🎁 Промокоды")],
            [KeyboardButton(text="ℹ️ Правила / FAQ")]
        ],
        resize_keyboard=True,
        persistent=True
    )

# Клавиатура отмены
def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, отправить")],
            [KeyboardButton(text="✏️ Редактировать")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Клавиатура для редактирования полей
def get_edit_fields_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Адрес")],
            [KeyboardButton(text="🕐 Время")],
            [KeyboardButton(text="👥 Гостей")],
            [KeyboardButton(text="💬 Комментарий")],
            [KeyboardButton(text="✅ Всё верно, отправить")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

# Клавиатура для отмены
def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )