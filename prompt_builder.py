from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")],
        [InlineKeyboardButton("🤖 О Direct Mode", callback_data="direct_info")],
    ])


def settings_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎭 Стиль Business", callback_data="prompt_business")],
        [InlineKeyboardButton("🎭 Стиль Direct", callback_data="prompt_direct")],
        [InlineKeyboardButton("✏️ Свой промпт", callback_data="custom_prompt")],
        [InlineKeyboardButton("🧠 База знаний", callback_data="knowledge")],
        [InlineKeyboardButton("👥 Контакты", callback_data="contacts")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")],
    ])
