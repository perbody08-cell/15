from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from database.crud import get_or_create_user
from sqlalchemy import select, and_
from database.models import Contact


async def contacts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню управления контактами (только для Business Mode)"""

    query = update.callback_query
    await query.answer()

    factory = context.bot_data["db_session_factory"]
    session: AsyncSession = factory()
    try:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)

        if not user.is_business_connected:
            await query.edit_message_text(
                "💼 Business Mode не подключён.\n\n"
                "Подключите его в настройках Telegram Business, чтобы управлять контактами.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings")]])
            )
            return

        result = await session.execute(
            select(Contact).where(Contact.owner_id == user.id).order_by(Contact.created_at.desc()).limit(20)
        )
        contacts = result.scalars().all()

        if not contacts:
            text = "👥 У вас пока нет контактов.\n\nКонтакты появятся автоматически, когда кто-то напишет вам."
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="settings")]]
        else:
            text = "👥 Ваши контакты (Business Mode):\n\n"
            keyboard = []
            for c in contacts:
                status = "🟢" if c.is_active else "🔴"
                name = c.first_name or c.username or f"ID:{c.telegram_user_id}"
                text += f"{status} {name} ({c.relationship_type})\n"
                keyboard.append([InlineKeyboardButton(
                    f"{status} {name}",
                    callback_data=f"contact_{c.id}"
                )])

            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="settings")])

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        await session.close()


async def contact_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали контакта"""

    query = update.callback_query
    await query.answer()

    contact_id = int(query.data.split("_")[1])

    factory = context.bot_data["db_session_factory"]
    session: AsyncSession = factory()
    try:
        # Проверяем принадлежность контакта текущему пользователю (защита от IDOR)
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        result = await session.execute(
            select(Contact).where(
                and_(Contact.id == contact_id, Contact.owner_id == user.id)
            )
        )
        contact = result.scalar_one_or_none()

        if not contact:
            await query.edit_message_text("Контакт не найден или недостаточно прав.")
            return

        name = contact.first_name or contact.username or f"ID:{contact.telegram_user_id}"

        text = (
            f"👤 {name}\n\n"
            f"Отношения: {contact.relationship_type}\n"
            f"Статус: {'🟢 Бот отвечает' if contact.is_active else '🔴 Бот отключён'}\n"
            f"Заметки: {contact.notes or 'Нет'}\n"
            f"Извлечённый стиль: {contact.extracted_style or 'Не анализировался'}"
        )

        keyboard = [
            [InlineKeyboardButton(
                "🔴 Отключить бота" if contact.is_active else "🟢 Включить бота",
                callback_data=f"toggle_contact_{contact.id}"
            )],
            [InlineKeyboardButton("🏷️ Тип отношений", callback_data=f"rel_contact_{contact.id}")],
            [InlineKeyboardButton("📝 Заметки", callback_data=f"notes_contact_{contact.id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="contacts")]
        ]

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        await session.close()


async def toggle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Включить/отключить бота для контакта"""

    query = update.callback_query
    await query.answer()

    contact_id = int(query.data.split("_")[2])

    factory = context.bot_data["db_session_factory"]
    session: AsyncSession = factory()
    try:
        # Проверяем принадлежность контакта текущему пользователю (защита от IDOR)
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        result = await session.execute(
            select(Contact).where(
                and_(Contact.id == contact_id, Contact.owner_id == user.id)
            )
        )
        contact = result.scalar_one_or_none()

        if not contact:
            await query.edit_message_text("Контакт не найден или недостаточно прав.")
            return

        from database.crud import update_contact
        await update_contact(session, contact_id, is_active=not contact.is_active)
    finally:
        await session.close()

    # Перезагружаем детали контакта
    update.callback_query.data = f"contact_{contact_id}"
    await contact_detail(update, context)
