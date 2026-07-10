import logging
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from settings import settings
from database.models import Base, Prompt
from handlers.business import handle_business_message, handle_business_connection
from handlers.direct import handle_direct_message, direct_mode_info
from handlers.admin import (
    settings_menu, select_prompt_business, select_prompt_direct,
    prompt_selected, custom_prompt_start, custom_prompt_received,
    knowledge_menu, knowledge_edit_start, knowledge_received,
    stats_callback, ENTERING_CUSTOM_PROMPT, ENTERING_KNOWLEDGE
)
from handlers.contacts import contacts_menu, contact_detail, toggle_contact

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from keyboards.inline import main_menu_keyboard
    await update.message.reply_text(
        "👋 Привет! Я AI-ассистент.

"
        "💼 Business Mode — отвечаю от вашего имени через Telegram Business
"
        "🤖 Direct Mode — общаюсь с вами напрямую

"
        "Выберите режим в меню ниже:",
        reply_markup=main_menu_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Используйте /start для начала.")


async def post_init(application):
    engine = application.bot_data["engine"]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created.")
    # Seed default prompts
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        from sqlalchemy import select
        from database.models import Prompt
        result = await session.execute(select(Prompt).where(Prompt.id == 1))
        if not result.scalar_one_or_none():
            session.add(Prompt(
                id=1,
                name="Стандартный",
                description="Стандартный дружелюбный стиль",
                system_prompt="Отвечай естественно, дружелюбно и по-человечески. Используй эмодзи умеренно. Будь краток, 1-3 предложения.",
                category="business",
                is_active=True
            ))
            session.add(Prompt(
                id=2,
                name="Дружелюбный",
                description="Дружелюбный AI-ассистент",
                system_prompt="Ты дружелюбный AI-ассистент. Общайся тепло, помогай с вопросами, будь честным о своих возможностях.",
                category="direct",
                is_active=True
            ))
            await session.commit()
            logger.info("Default prompts seeded.")


def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    application = (
        ApplicationBuilder()
        .token(settings.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.bot_data["db_session_factory"] = async_session
    application.bot_data["engine"] = engine

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    custom_prompt_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(custom_prompt_start, pattern="^custom_prompt$")],
        states={
            ENTERING_CUSTOM_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_prompt_received)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("Отменено."))],
    )

    knowledge_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(knowledge_edit_start, pattern="^knowledge_edit$")],
        states={
            ENTERING_KNOWLEDGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, knowledge_received)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("Отменено."))],
    )

    application.add_handler(custom_prompt_conv)
    application.add_handler(knowledge_conv)

    application.add_handler(CallbackQueryHandler(settings_menu, pattern="^settings$"))
    application.add_handler(CallbackQueryHandler(select_prompt_business, pattern="^prompt_business$"))
    application.add_handler(CallbackQueryHandler(select_prompt_direct, pattern="^prompt_direct$"))
    application.add_handler(CallbackQueryHandler(prompt_selected, pattern="^prompt_(business|direct)_"))
    application.add_handler(CallbackQueryHandler(knowledge_menu, pattern="^knowledge$"))
    application.add_handler(CallbackQueryHandler(stats_callback, pattern="^stats$"))
    application.add_handler(CallbackQueryHandler(contacts_menu, pattern="^contacts$"))
    application.add_handler(CallbackQueryHandler(contact_detail, pattern="^contact_\d+$"))
    application.add_handler(CallbackQueryHandler(toggle_contact, pattern="^toggle_contact_\d+$"))
    application.add_handler(CallbackQueryHandler(direct_mode_info, pattern="^direct_info$"))
    application.add_handler(CallbackQueryHandler(start_command, pattern="^main_menu$"))

    application.add_handler(MessageHandler(
        filters.UpdateType.BUSINESS_MESSAGE & filters.TEXT,
        handle_business_message
    ))
    application.add_handler(MessageHandler(
        filters.StatusUpdate.BUSINESS_CONNECTIONS,
        handle_business_connection
    ))

    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND,
        handle_direct_message
    ))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
