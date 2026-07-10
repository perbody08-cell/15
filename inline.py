from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from database.crud import (
    get_or_create_user, get_or_create_direct_chat, get_direct_chat_history,
    add_direct_message, update_direct_chat
)
from services.llm import get_llm
from services.prompt_builder import PromptBuilder
from settings import settings
import logging

logger = logging.getLogger(__name__)


async def handle_direct_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик прямых сообщений пользователю боту (не Business)"""

    if not settings.ENABLE_DIRECT_MODE:
        return

    # Пропускаем команды
    if update.message and update.message.text and update.message.text.startswith("/"):
        return

    # Пропускаем сообщения из Business Connection
    if update.business_message:
        return

    # Работаем только в личных чатах
    if update.effective_chat.type != "private":
        return

    factory = context.bot_data["db_session_factory"]
    session: AsyncSession = factory()
    try:
        # Получаем или создаём пользователя
        user = await get_or_create_user(
            session,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name
        )

        # Проверяем, включён ли Direct Mode
        if not user.direct_mode_enabled:
            return

        # Получаем или создаём direct чат
        chat = await get_or_create_direct_chat(session, user.id)

        # Сохраняем сообщение пользователя
        await add_direct_message(
            session,
            chat_id=chat.id,
            sender_type="user",
            text=update.message.text or ""
        )

        # Показываем typing
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        # Получаем историю
        history = await get_direct_chat_history(session, chat.id, limit=settings.MAX_CONTEXT_MESSAGES)
        history_dicts = [{"sender_type": h.sender_type, "text": h.text} for h in history]

        # Строим промпт
        system_prompt = PromptBuilder.build_direct_prompt(
            user=user,
            chat=chat,
            prompt=user.prompt
        )
        messages = PromptBuilder.build_messages(history_dicts, update.message.text or "")

        # Генерируем ответ
        llm = get_llm(user.llm_provider, user.llm_api_key)

        try:
            response_text = await llm.generate(
                system_prompt,
                messages,
                mode="direct",
                user_settings={"user_id": user.id, "chat_id": chat.id}
            )

            # Отправляем ответ
            await update.message.reply_text(response_text)

            # Сохраняем ответ бота
            await add_direct_message(
                session,
                chat_id=chat.id,
                sender_type="bot",
                text=response_text,
                llm_model=user.llm_provider
            )

        except Exception as e:
            logger.error(f"Direct LLM Error: {e}", exc_info=True)
            await update.message.reply_text(
                "⚠️ Произошла ошибка при генерации ответа. Попробуйте позже."
            )
    finally:
        await session.close()


async def direct_mode_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о Direct Mode"""

    query = update.callback_query
    await query.answer()

    text = (
        "🤖 Direct Mode — общение с ботом\n\n"
        "В этом режиме вы просто общаетесь со мной как с AI-ассистентом.\n\n"
        "💡 Возможности:\n"
        "• Задавайте любые вопросы\n"
        "• Просите помочь с задачами\n"
        "• Обсуждайте идеи\n"
        "• Практикуйте языки\n"
        "• Получайте советы\n\n"
        "⚙️ Настройки:\n"
        "• Выберите стиль общения\n"
        "• Настройте свою персону\n"
        "• Укажите интересы для персонализации\n\n"
        "💼 Также доступен Business Mode — бот будет отвечать от вашего имени в личных чатах через Telegram Business."
    )

    from keyboards.inline import main_menu_keyboard
    await query.edit_message_text(text, reply_markup=main_menu_keyboard())
