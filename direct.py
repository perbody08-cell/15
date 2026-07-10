from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy.ext.asyncio import AsyncSession
from database.crud import get_prompts, update_user_prompt, update_user_knowledge, get_user_stats, get_or_create_user
from database.models import User

ENTERING_CUSTOM_PROMPT, ENTERING_KNOWLEDGE = range(2)


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    from keyboards.inline import settings_menu_keyboard
    text = (
        "⚙️ Настройки

"
        "Здесь вы можете настроить оба режима работы бота:

"
        "💼 Business Mode — как бот отвечает от вашего имени
"
        "🤖 Direct Mode — как бот общается с вами напрямую"
    )
    if query:
        await query.edit_message_text(text, reply_markup=settings_menu_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=settings_menu_keyboard())


async def select_prompt_business(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    factory = context.bot_data["db_session_factory"]
    session: AsyncSession = factory()
    try:
        prompts = await get_prompts(session, category="business")
        keyboard = []
        for prompt in prompts:
            keyboard.append([InlineKeyboardButton(f"{prompt.name}", callback_data=f"prompt_business_{prompt.id}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="settings")])
        await query.edit_message_text(
            "🎭 Выберите стиль для Business Mode:

"
            "Это определит, как бот будет отвечать от вашего имени в личных чатах.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    finally:
        await session.close()


async def select_prompt_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    factory = context.bot_data["db_session_factory"]
    session: AsyncSession = factory()
    try:
        prompts = await get_prompts(session, category="direct")
        keyboard = []
        for prompt in prompts:
            keyboard.append([InlineKeyboardButton(f"{prompt.name}", callback_data=f"prompt_direct_{prompt.id}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="settings")])
        await query.edit_message_text(
            "🎭 Выберите стиль для Direct Mode:

"
            "Это определит, как я буду общаться с вами напрямую.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    finally:
        await session.close()


async def prompt_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    mode = data[1]
    prompt_id = int(data[2])
    factory = context.bot_data["db_session_factory"]
    session: AsyncSession = factory()
    try:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        from database.crud import get_prompt_by_id
        prompt = await get_prompt_by_id(session, prompt_id)
        await update_user_prompt(session, user.id, prompt_id)
        mode_text = "Business Mode" if mode == "business" else "Direct Mode"
        await query.edit_message_text(
            f"✅ Стиль «{prompt.name}» выбран для {mode_text}!

"
            f"Описание: {prompt.description or 'Нет описания'}

"
            f"Промпт: {prompt.system_prompt[:200]}...",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings")]])
        )
    finally:
        await session.close()


async def custom_prompt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✏️ Напишите свой промпт

"
        "Опишите, как бот должен отвечать.

"
        "💼 Для Business Mode:
"
        "«Отвечай кратко, используй сленг типа 'крч', 'типа'. "
        "Любишь эмодзи 😎. С друзьями — неформально.»

"
        "🤖 Для Direct Mode:
"
        "«Общайся как мудрый наставник, давай развёрнутые "
        "советы, используй примеры из жизни.»

"
        "Отправьте текст или /cancel для отмены."
    )
    return ENTERING_CUSTOM_PROMPT


async def custom_prompt_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    factory = context.bot_data["db_session_factory"]
    session: AsyncSession = factory()
    try:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        user.custom_prompt = update.message.text
        await session.commit()
        await update.message.reply_text(
            f"✅ Промпт сохранён!

Текст: {update.message.text[:200]}...",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 В настройки", callback_data="settings")]])
        )
    finally:
        await session.close()
    return ConversationHandler.END


async def knowledge_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    factory = context.bot_data["db_session_factory"]
    session: AsyncSession = factory()
    try:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        knowledge = user.global_knowledge or {}
        knowledge_text = "
".join([f"• {k}: {v}" for k, v in knowledge.items()]) or "Пока нет записей."
        keyboard = [
            [InlineKeyboardButton("➕ Добавить/изменить", callback_data="knowledge_edit")],
            [InlineKeyboardButton("🔙 Назад", callback_data="settings")]
        ]
        await query.edit_message_text(
            f"🧠 База знаний

"
            f"Эта информация используется в обоих режимах:

"
            f"{knowledge_text}

"
            f"💼 Business: помогает боту отвечать правдоподобно от вашего имени
"
            f"🤖 Direct: помогает мне лучше понимать ваш контекст",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    finally:
        await session.close()


async def knowledge_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📝 Отправьте информацию о себе

"
        "Формат: Ключ - Значение (каждая строка — новый пункт)

"
        "Пример:
"
        "Работа - Программист в Яндексе
"
        "Город - Москва
"
        "Хобби - Играю в футбол по выходным
"
        "Семья - Женат, двое детей
"
        "Возраст - 28 лет
"
        "Интересы - AI, путешествия, кулинария

"
        "Отправьте текст или /cancel"
    )
    return ENTERING_KNOWLEDGE


async def knowledge_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    factory = context.bot_data["db_session_factory"]
    session: AsyncSession = factory()
    try:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        knowledge = {}
        for line in update.message.text.split("
"):
            if " - " in line:
                key, value = line.split(" - ", 1)
                knowledge[key.strip()] = value.strip()
        await update_user_knowledge(session, user.id, knowledge)
        await update.message.reply_text(
            f"✅ База знаний обновлена! ({len(knowledge)} пунктов)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 В настройки", callback_data="settings")]])
        )
    finally:
        await session.close()
    return ConversationHandler.END


async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    factory = context.bot_data["db_session_factory"]
    session: AsyncSession = factory()
    try:
        user = await get_or_create_user(session, telegram_id=update.effective_user.id)
        stats = await get_user_stats(session, user.id)
        await query.edit_message_text(
            f"📊 Статистика

"
            f"💼 Business Mode:
"
            f"  Контактов: {stats['contacts']}
"
            f"  Сессий: {stats['sessions']}
"
            f"  Сообщений: {stats['messages']}
"
            f"  Подключен: {'✅' if user.is_business_connected else '❌'}

"
            f"🤖 Direct Mode:
"
            f"  Сообщений: {stats['direct_messages']}
"
            f"  Включён: {'✅' if user.direct_mode_enabled else '❌'}

"
            f"⚙️ LLM: {user.llm_provider}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings")]])
        )
    finally:
        await session.close()
