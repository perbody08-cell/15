import random
from typing import List, Dict
from settings import settings


class MockLLM:
    """Заглушка для тестирования"""

    BUSINESS_RESPONSES = [
        "Привет! Сейчас не могу ответить подробно, но скоро свяжусь.",
        "Понял тебя, давай обсудим это позже?",
        "Хм, интересно... Расскажи подробнее.",
        "Да, согласен. Что думаешь по этому поводу?",
        "Окей, договорились! 👍",
        "Слушай, я сейчас занят, отвечу чуть позже.",
        "Хаха, точно! 😄",
        "Не уверен, надо подумать...",
    ]

    DIRECT_RESPONSES = [
        "Привет! Я твой AI-ассистент. Чем могу помочь?",
        "Интересный вопрос! Давай разберёмся вместе.",
        "Я пока учусь, но постараюсь помочь лучше, чем могу!",
        "Хм, давай подумаем над этим...",
        "Отличная тема! Вот что я знаю...",
        "Я здесь, чтобы помочь. Спроси что угодно!",
    ]

    async def generate(self, system_prompt: str, messages: List[Dict], 
                     mode: str = "business", user_settings: dict = None) -> str:
        await __import__('asyncio').sleep(0.5)

        if mode == "direct":
            return random.choice(self.DIRECT_RESPONSES)
        return random.choice(self.BUSINESS_RESPONSES)

    async def analyze_style(self, chat_history: List[str]) -> Dict:
        return {
            "favorite_words": ["привет", "окей", "давай"],
            "emoji_frequency": "средняя",
            "response_length": "средние",
            "tone": "дружелюбный",
            "formality": "неформальный"
        }


class AnthropicLLM:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4.6"):
        self.api_key = api_key
        self.model = model

    async def generate(self, system_prompt: str, messages: List[Dict], 
                       mode: str = "business", user_settings: dict = None) -> str:
        raise NotImplementedError("Claude API не настроен")

    async def analyze_style(self, chat_history: List[str]) -> Dict:
        raise NotImplementedError("Claude API не настроен")


class OpenAILLM:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    async def generate(self, system_prompt: str, messages: List[Dict], 
                       mode: str = "business", user_settings: dict = None) -> str:
        raise NotImplementedError("OpenAI API не настроен")

    async def analyze_style(self, chat_history: List[str]) -> Dict:
        raise NotImplementedError("OpenAI API не настроен")


class LocalLLM:
    def __init__(self, base_url: str, model: str = "local-model"):
        self.base_url = base_url
        self.model = model

    async def generate(self, system_prompt: str, messages: List[Dict], 
                       mode: str = "business", user_settings: dict = None) -> str:
        raise NotImplementedError("Локальный LLM не настроен")

    async def analyze_style(self, chat_history: List[str]) -> Dict:
        raise NotImplementedError("Локальный LLM не настроен")


def get_llm(provider: str = None, api_key: str = None):
    provider = provider or settings.LLM_PROVIDER

    if provider == "anthropic":
        return AnthropicLLM(api_key=api_key or settings.LLM_API_KEY, model=settings.LLM_MODEL)
    elif provider == "openai":
        return OpenAILLM(api_key=api_key or settings.LLM_API_KEY, model=settings.LLM_MODEL)
    elif provider == "local":
        return LocalLLM(base_url=settings.LLM_BASE_URL, model=settings.LLM_MODEL)
    else:
        return MockLLM()
