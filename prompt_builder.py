from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Общение с ботом", callback_data="direct_mode")],
        [InlineKeyboardButton("💼 Business Mode", callback_data="business_info")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")],
        [InlineKeyboardButton("📖 Инструкция", callback_data="help")],
    ])


def settings_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎭 Стиль ответов (Business)", callback_data="select_prompt_business")],
        [InlineKeyboardButton("🎭 Стиль общения (Direct)", callback_data="select_prompt_direct")],
        [InlineKeyboardButton("📝 Свой промпт", callback_data="custom_prompt")],
        [InlineKeyboardButton("🧠 База знаний", callback_data="knowledge")],
        [InlineKeyboardButton("👥 Контакты (Business)", callback_data="contacts")],
        [InlineKeyboardButton("🤖 Настройки LLM", callback_data="llm_settings")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")],
    ])


def back_button(callback_data="settings"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад", callback_data=callback_data)]
    ])


def mode_selection_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💼 Business Mode", callback_data="business_info")],
        [InlineKeyboardButton("🤖 Direct Mode (общение)", callback_data="direct_mode_info")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")],
    ])
