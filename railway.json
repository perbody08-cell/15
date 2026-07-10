import sys
sys.path.insert(0, '/app')

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes, BusinessConnectionHandler
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from settings import settings
from database.models import Base, Prompt
from database.crud import get_or_create_user

from handlers.business import handle_business_message, handle_business_connection
from handlers.direct import handle_direct_message, direct_mode_info
from handlers.settings import (
    settings_menu, select_prompt_business, select_prompt_direct, prompt_selected,
    custom_prompt_start, custom_prompt_received,
    knowledge_menu, knowledge_edit_start, knowledge_received,
    stats_callback
)
from handlers.contacts import contacts_menu, contact_detail, toggle_contact
from handlers.admin import admin_panel, admin_stats

from keyboards.inline import main_menu_keyboard, mode_selection_keyboard

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ENTERING_CUSTOM_PROMPT, ENTERING_KNOWLEDGE = range(2)


async def init_db():
    """Инициализация БД и дефолтных промптов"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(select(Prompt).where(Prompt.id == 1))
        if not result.scalar_one_or_none():
            default_prompts = [
                # === BUSINESS PROMPTS ===
                Prompt(
                    id=1,
                    name="🎭 Дружелюбный",
                    description="Тёплый, неформальный стиль",
                    system_prompt="Ты — дружелюбный и открытый человек. Отвечай тепло, используй эмодзи, задавай вопросы собеседнику. Тон: неформальный, как с хорошим знакомым.",
                    category="business"
                ),
                Prompt(
                    id=2,
                    name="💼 Деловой",
                    description="Кратко, по делу, профессионально",
                    system_prompt="Ты — деловой человек. Отвечай кратко, по существу, без лишних эмодзи. Тон: профессиональный, вежливый, но не холодный.",
                    category="business"
                ),
                Prompt(
                    id=3,
                    name="🏠 Семья",
                    description="Тепло, забота, внимание к деталям",
                    system_prompt="Ты — семейный человек. Отвечай с заботой, интересуйся делами собеседника, используй тёплые слова. Тон: ласковый, внимательный.",
                    category="business"
                ),
                Prompt(
                    id=4,
                    name="😎 Саркастичный",
                    description="С иронией, но без злобы",
                    system_prompt="Ты — человек с чувством юмора. Отвечай с лёгкой иронией, остроумно, но не грубо. Любишь поддразнивать друзей. Тон: игривый, саркастичный.",
                    category="business"
                ),
                Prompt(
                    id=5,
                    name="🤫 Лаконичный",
                    description="Коротко, по делу, без воды",
                    system_prompt="Ты — лаконичный человек. Отвечай максимально коротко, 1-2 слова или предложение. Без эмодзи, без лишних слов. Тон: сдержанный.",
                    category="business"
                ),
                # === DIRECT PROMPTS ===
                Prompt(
                    id=6,
                    name="🤖 Универсальный ассистент",
                    description="Полезный, дружелюбный AI",
                    system_prompt="Ты — умный и дружелюбный AI-ассистент. Помогай с любыми вопросами, давай развёрнутые ответы, будь терпеливым. Тон: профессиональный, но тёплый.",
                    category="direct"
                ),
                Prompt(
                    id=7,
                    name="🧙 Мудрый наставник",
                    description="Философский, глубокий подход",
                    system_prompt="Ты — мудрый наставник. Давай глубокие, осмысленные ответы. Используй метафоры, примеры из жизни. Тон: спокойный, философский, вдохновляющий.",
                    category="direct"
                ),
                Prompt(
                    id=8,
                    name="⚡ Быстрый помощник",
                    description="Кратко, по делу, без воды",
                    system_prompt="Ты — эффективный помощник. Отвечай кратко и по существу. Без лишних слов, только факты и действия. Тон: деловой, энергичный.",
                    category="direct"
                ),
                Prompt(
                    id=9,
                    name="🎨 Творческий собеседник",
                    description="Воображение, креатив, нестандартные идеи",
                    system_prompt="Ты — творческий собеседник. Предлагай нестандартные идеи, используй образные сравнения, вдохновляй на новое. Тон: игривый, креативный, энтузиаст.",
                    category="direct"
                ),
                Prompt(
                    id=10,
                    name="🤝 Друг и собеседник",
                    description="Неформально, с эмпатией, как друг",
                    system_prompt="Ты — хороший друг. Общайся неформально, с эмпатией, поддерживай в трудную минуту. Используй сленг, шутки, эмодзи. Тон: тёплый, искренний.",
                    category="direct"
                ),
            ]
            for p in default_prompts:
                session.add(p)
            await session.commit()

    return engine


async def post_init(application: Application):
    """Инициализация после старта бота"""
    engine = await init_db()
    application.bot_data["engine"] = engine
    application.bot_data["db_session_factory"] = async_sessionmaker(engine, expire_on_commit=False)
    logger.info("✅ База данных инициализирована")


async def get_db_session(context: ContextTypes.DEFAULT_TYPE) -> AsyncSession:
    """Получение сессии БД"""
    factory = context.bot_data["db_session_factory"]
    return factory()


# ========== COMMANDS ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    session = await get_db_session(context)

    user = await get_or_create_user(
        session,
        telegram_id=update.effective_user.id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name
    )

    text = (
        f"👋 Привет, {user.first_name or 'друг'}!\n\n"
        "Я — AI-бот с двумя режимами работы:\n\n"
        "💼 **Business Mode**\n"
        "Подключи меня к Telegram Business — и я буду отвечать на сообщения от твоего имени в личных чатах.\n\n"
        "🤖 **Direct Mode**\n"
        "Просто общайся со мной напрямую как с AI-ассистентом. Задавай вопросы, проси помощь, обсуждай идеи.\n\n"
        "⚙️ Настрой стиль, базу знаний и другие параметры в меню.\n"
        "⚠️ Сейчас работаю в тестовом режиме (заглушка LLM)."
    )

    await update.message.reply_text(text, reply_markup=main_menu_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    text = (
        "📖 **Инструкция**\n\n"
        "**Business Mode:**\n"
        "1. Перейди в Настройки → Telegram Business → Автоматизация чатов\n"
        "2. Введи @username бота\n"
        "3. Выбери, к каким чатам бот будет иметь доступ\n"
        "4. Настрой стиль и базу знаний в этом боте\n\n"
        "**Direct Mode:**\n"
        "Просто пиши мне сообщения — я отвечу как AI-ассистент.\n\n"
        "**Команды:**\n"
        "/start — главное меню\n"
        "/help — эта инструкция\n"
        "/settings — настройки\n"
        "/admin — админ-панель (только для админов)\n\n"
        "**Настройки:**\n"
        "• Стиль ответов — выбери или создай свой промпт\n"
        "• База знаний — расскажи о себе для персонализации\n"
        "• Контакты — управляй, для кого бот отвечает (Business)\n"
        "• LLM — выбери модель (позже)"
    )

    await update.message.reply_text(text)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /settings"""
    await settings_menu(update, context)


# ========== CALLBACK HANDLERS ==========

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню"""
    query = update.callback_query
    await query.answer()

    text = "🏠 Главное меню\n\nВыбери режим или перейди к настройкам:"

    await query.edit_message_text(text, reply_markup=main_menu_keyboard())


async def business_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о Business Mode"""
    query = update.callback_query
    await query.answer()

    text = (
        "💼 **Business Mode**\n\n"
        "Бот отвечает на сообщения **от твоего имени** в личных чатах через Telegram Business.\n\n"
        "**Как подключить:**\n"
        "1. Нужен Telegram Business (платная подписка)\n"
        "2. Настройки → Автоматизация чатов → Добавить бота\n"
        "3. Введи @username этого бота\n"
        "4. Выбери чаты, к которым бот будет иметь доступ\n\n"
        "**Что умеет:**\n"
        "• Отвечать в твоём стиле (настраивается)\n"
        "• Использовать базу знаний о тебе\n"
        "• Учитывать контекст переписки\n"
        "• Работать с разными контактами по-разному\n\n"
        "**Безопасность:**\n"
        "Ты сам решаешь, к каким чатам бот имеет доступ. Можно отключить в любой момент."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Настройки Business", callback_data="settings")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ])

    await query.edit_message_text(text, reply_markup=keyboard)


async def mode_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор режима"""
    query = update.callback_query
    await query.answer()

    text = "🎯 **Выбор режима**\n\nКак ты хочешь использовать бота?"

    await query.edit_message_text(text, reply_markup=mode_selection_keyboard())


# ========== ERROR HANDLER ==========

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}", exc_info=True)
    if update and update.effective_message:
        await update.effective_message.reply_text("⚠️ Произошла ошибка. Попробуй позже.")


# ========== MAIN ==========

def main():
    application = Application.builder().token(settings.BOT_TOKEN).post_init(post_init).build()

    # === Conversation Handlers ===
    custom_prompt_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(custom_prompt_start, pattern="^custom_prompt$")],
        states={
            ENTERING_CUSTOM_PROMPT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, custom_prompt_received)
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("Отменено"))],
    )

    knowledge_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(knowledge_edit_start, pattern="^knowledge_edit$")],
        states={
            ENTERING_KNOWLEDGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, knowledge_received)
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("Отменено"))],
    )

    # === Commands ===
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("admin", admin_panel))

    # === Conversations ===
    application.add_handler(custom_prompt_conv)
    application.add_handler(knowledge_conv)

    # === Callback Queries ===
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(business_info_callback, pattern="^business_info$"))
    application.add_handler(CallbackQueryHandler(mode_selection_callback, pattern="^mode_select$"))

    # Settings
    application.add_handler(CallbackQueryHandler(settings_menu, pattern="^settings$"))
    application.add_handler(CallbackQueryHandler(select_prompt_business, pattern="^select_prompt_business$"))
    application.add_handler(CallbackQueryHandler(select_prompt_direct, pattern="^select_prompt_direct$"))
    application.add_handler(CallbackQueryHandler(prompt_selected, pattern=r"^prompt_(business|direct)_"))
    application.add_handler(CallbackQueryHandler(knowledge_menu, pattern="^knowledge$"))
    application.add_handler(CallbackQueryHandler(stats_callback, pattern="^stats$"))

    # Contacts
    application.add_handler(CallbackQueryHandler(contacts_menu, pattern="^contacts$"))
    application.add_handler(CallbackQueryHandler(contact_detail, pattern=r"^contact_\d+$"))
    application.add_handler(CallbackQueryHandler(toggle_contact, pattern=r"^toggle_contact_\d+$"))

    # Direct Mode
    application.add_handler(CallbackQueryHandler(direct_mode_info, pattern="^direct_mode$"))
    application.add_handler(CallbackQueryHandler(direct_mode_info, pattern="^direct_mode_info$"))

    # Admin
    application.add_handler(CallbackQueryHandler(admin_stats, pattern="^admin_stats$"))

    # === Business Connection ===
    if settings.ENABLE_BUSINESS_MODE:
        application.add_handler(BusinessConnectionHandler(handle_business_connection))
        application.add_handler(MessageHandler(
            filters.UpdateType.BUSINESS_MESSAGE,
            handle_business_message
        ))

    # === Direct Mode (обычные сообщения в личке) ===
    if settings.ENABLE_DIRECT_MODE:
        application.add_handler(MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND,
            handle_direct_message
        ))

    # === Errors ===
    application.add_error_handler(error_handler)

    logger.info("🚀 Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
