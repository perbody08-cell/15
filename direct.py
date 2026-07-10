from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from database.crud import get_user_by_business_conn, get_or_create_contact, get_or_create_chat_session, get_chat_history, add_message, log_business_connection
from services.llm import get_llm
from services.prompt_builder import PromptBuilder
from settings import settings


async def handle_business_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.business_message:
        return
    if not settings.ENABLE_BUSINESS_MODE:
        return
    business_msg = update.business_message
    business_conn_id = business_msg.business_connection_id
    factory = context.bot_data["db_session_factory"]
    session: AsyncSession = factory()
    try:
        user = await get_user_by_business_conn(session, business_conn_id)
        if not user:
            return
        contact_user = business_msg.from_user
        contact = await get_or_create_contact(session, owner_id=user.id, telegram_user_id=contact_user.id, username=contact_user.username, first_name=contact_user.first_name, last_name=contact_user.last_name)
        if not contact.is_active:
            return
        chat_session = await get_or_create_chat_session(session, owner_id=user.id, chat_id=business_msg.chat.id, contact_id=contact.id, session_type="business")
        await add_message(session, session_id=chat_session.id, sender_type="contact", text=business_msg.text or "", contact_id=contact.id)
        history = await get_chat_history(session, chat_session.id, limit=settings.MAX_CONTEXT_MESSAGES)
        history_dicts = [{"sender_type": h.sender_type, "text": h.text} for h in history]
        system_prompt = PromptBuilder.build_business_prompt(user=user, contact=contact, prompt=user.prompt)
        messages = PromptBuilder.build_messages(history_dicts, business_msg.text or "")
        llm = get_llm(user.llm_provider, user.llm_api_key)
        try:
            response_text = await llm.generate(system_prompt, messages, mode="business", user_settings={"user_id": user.id, "contact_id": contact.id})
            await context.bot.send_message(chat_id=business_msg.chat.id, text=response_text, business_connection_id=business_conn_id)
            await add_message(session, session_id=chat_session.id, sender_type="bot", text=response_text, contact_id=contact.id, llm_model=user.llm_provider)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Business LLM Error: {e}", exc_info=True)
        from datetime import datetime
        chat_session.last_message_at = datetime.utcnow()
        await session.commit()
    finally:
        await session.close()


async def handle_business_connection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.business_connection:
        return
    conn = update.business_connection
    factory = context.bot_data["db_session_factory"]
    session: AsyncSession = factory()
    try:
        from database.crud import get_or_create_user, update_business_connection
        user = await get_or_create_user(session, telegram_id=conn.user_chat_id, first_name=conn.user.first_name if conn.user else None)
        if conn.is_enabled:
            await update_business_connection(session, user.id, conn.id)
            await log_business_connection(session, user.id, conn.id, "connected", {"can_reply": conn.can_reply, "user_chat_id": conn.user_chat_id})
            await context.bot.send_message(chat_id=conn.user_chat_id, text="✅ Business-аккаунт подключен!

Бот теперь будет отвечать на сообщения от вашего имени в личных чатах.

📋 Что настроить:
• Стиль ответов — как бот будет писать от вашего имени
• База знаний — информация о вас для правдоподобных ответов
• Контакты — для кого включить/выключить автоответ

⚠️ Сейчас работает в тестовом режиме (заглушка LLM).")
        else:
            await log_business_connection(session, user.id, conn.id, "disconnected")
            user.is_business_connected = False
            await session.commit()
            await context.bot.send_message(chat_id=conn.user_chat_id, text="❌ Business-аккаунт отключен. Бот больше не отвечает за вас.")
    finally:
        await session.close()
