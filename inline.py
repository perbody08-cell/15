from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from database.models import User, Message, DirectMessage, BusinessConnectionLog
from settings import settings


def is_admin(user_id: int) -> bool:
    return user_id in settings.get_admin_ids


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ-панель"""

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Доступ запрещён")
        return

    keyboard = [
        [InlineKeyboardButton("📊 Общая статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("💼 Business логи", callback_data="admin_business_logs")],
        [InlineKeyboardButton("🤖 Direct статистика", callback_data="admin_direct_stats")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
    ]

    await update.message.reply_text("🔐 Админ-панель", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Общая статистика — только для администраторов"""

    query = update.callback_query
    await query.answer()

    # Повторная проверка прав — callback может быть вызван напрямую
    if not is_admin(update.effective_user.id):
        await query.edit_message_text("⛔ Доступ запрещён")
        return

    factory = context.bot_data["db_session_factory"]
    session: AsyncSession = factory()
    try:
        users_count = await session.execute(select(func.count(User.id)))
        active_business = await session.execute(
            select(func.count(User.id)).where(User.is_business_connected == True)
        )
        total_messages = await session.execute(select(func.count(Message.id)))
        total_direct = await session.execute(select(func.count(DirectMessage.id)))

        text = (
            f"📊 Общая статистика\n\n"
            f"Всего пользователей: {users_count.scalar()}\n"
            f"Business подключён: {active_business.scalar()}\n"
            f"Business сообщений: {total_messages.scalar()}\n"
            f"Direct сообщений: {total_direct.scalar()}\n"
            f"Всего сообщений: {total_messages.scalar() + total_direct.scalar()}"
        )

        await query.edit_message_text(text)
    finally:
        await session.close()
