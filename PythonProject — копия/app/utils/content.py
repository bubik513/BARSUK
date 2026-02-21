from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.database import ContentCategory, ContentItem


async def get_categories(db: AsyncSession):
    """Получение активных категорий"""
    stmt = select(ContentCategory).where(
        ContentCategory.is_active == True
    ).order_by(ContentCategory.order)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_category_items(db: AsyncSession, category_id: int):
    """Получение позиций категории"""
    stmt = select(ContentItem).where(
        ContentItem.category_id == category_id,
        ContentItem.is_active == True
    ).order_by(ContentItem.order)
    result = await db.execute(stmt)
    return result.scalars().all()


async def format_category_text(category, items):
    """Форматирование текста категории"""
    text = f"<b>{category.name}</b>\n\n"

    for item in items:
        text += f"• <b>{item.name}</b>\n"
        if item.description:
            text += f"  {item.description}\n"
        text += f"  {item.price_display}\n\n"

    return text