from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey, JSON, BigInteger, DECIMAL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime
import enum
from sqlalchemy import select

from config import Config

Base = declarative_base()


# Статусы пользователя согласно ТЗ
class UserStatus(enum.Enum):
    NEW = "NEW"
    AGE_PENDING = "AGE_PENDING"
    ACTIVE = "ACTIVE"
    BLOCKED_UNDERAGE = "BLOCKED_UNDERAGE"
    BLOCKED_ADMIN = "BLOCKED_ADMIN"
    DELETED = "DELETED"


class User(Base):
    __tablename__ = "barsuk_app_telegramuser"

    id = Column(Integer, primary_key=True, index=True)  # Это первичный ключ
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    language_code = Column(String(10), default="ru")
    phone = Column(String(20), nullable=True)
    status = Column(Enum(UserStatus), default=UserStatus.NEW)
    is_18_confirmed = Column(Boolean, default=False)
    consent_accepted = Column(Boolean, default=False)
    consent_version = Column(String(50), nullable=True)
    consent_accepted_at = Column(DateTime, nullable=True)
    birth_date = Column(DateTime, nullable=True)
    city = Column(String(100), default="Тюмень")
    source = Column(String(100), nullable=True)
    points = Column(Integer, default=0)
    level = Column(String(20), default="Bronze")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Связи
    events = relationship("Event", back_populates="user", foreign_keys="[Event.user_id]")
    requests = relationship("Request", back_populates="user", foreign_keys="[Request.user_id]")


class Event(Base):
    __tablename__ = "barsuk_app_event"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("barsuk_app_telegramuser.id"))  # Внешний ключ на id, а не на telegram_id!
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="events", foreign_keys=[user_id])


class Request(Base):
    __tablename__ = "barsuk_app_request"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("barsuk_app_telegramuser.id"))  # Внешний ключ на id!
    request_type = Column(String(50), nullable=False)
    data = Column(JSON, nullable=True)
    status = Column(String(20), default="new")
    manager_notes = Column(Text, nullable=True)
    assigned_to = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="requests", foreign_keys=[user_id])


class ContentCategory(Base):
    __tablename__ = "barsuk_app_contentcategory"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("ContentItem", back_populates="category", cascade="all, delete-orphan")


class ContentItem(Base):
    __tablename__ = "barsuk_app_contentitem"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("barsuk_app_contentcategory.id"))
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(10, 2), nullable=True)
    image = Column(String(500), nullable=True)
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("ContentCategory", back_populates="items")

    @property
    def price_display(self):
        if self.price:
            return f"{self.price} ₽"
        return "Цена по запросу"


# Настройки подключения к PostgreSQL
DATABASE_URL = f"postgresql+asyncpg://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}/{Config.DB_NAME}"
engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Проверка подключения к БД"""
    async with engine.begin() as conn:
        pass
    print("✅ Подключение к базе данных установлено")


async def get_db():
    async with async_session() as session:
        async with session.begin():
            yield session


async def create_user(db: AsyncSession, telegram_user_id: str, username: str,
                      first_name: str = None, last_name: str = None,
                      language_code: str = "ru"):
    """
    Создать пользователя, если его ещё нет в базе данных.
    """
    telegram_id = int(telegram_user_id)

    # Проверяем существующего пользователя
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        existing_user.last_activity = datetime.utcnow()
        await db.commit()
        return existing_user

    # Создаем нового пользователя
    new_user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        language_code=language_code,
        status=UserStatus.NEW,
        created_at=datetime.utcnow(),
        last_activity=datetime.utcnow()
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Логируем событие
    await log_event(db, telegram_id, "bot_start")

    return new_user


async def log_event(db: AsyncSession, telegram_id: int, event_type: str, event_data: dict = None):
    """Логирование события пользователя"""
    # Сначала находим пользователя по telegram_id, чтобы получить его id
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        print(f"⚠️ Пользователь {telegram_id} не найден, событие {event_type} не записано")
        return

    # Создаем событие с правильным user_id (внутренний id, а не telegram_id)
    event = Event(
        user_id=user.id,  # Вот ключевое исправление!
        event_type=event_type,
        event_data=event_data or {},
        created_at=datetime.utcnow()
    )
    db.add(event)
    await db.commit()


async def confirm_age_and_save_phone(db: AsyncSession, telegram_user_id: str, phone: str,
                                     consent_version: str = "1.0"):
    """
    Подтвердить возраст, согласие и сохранить номер телефона пользователя.
    """
    telegram_id = int(telegram_user_id)

    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        user.is_18_confirmed = True
        user.phone = phone
        user.consent_accepted = True
        user.consent_version = consent_version
        user.consent_accepted_at = datetime.utcnow()
        user.status = UserStatus.ACTIVE
        user.last_activity = datetime.utcnow()

        await db.commit()

        # Логируем события
        await log_event(db, telegram_id, "age_confirmed")
        await log_event(db, telegram_id, "consent_accepted", {"version": consent_version})
        await log_event(db, telegram_id, "phone_captured", {"phone": phone})

        return user

    return None