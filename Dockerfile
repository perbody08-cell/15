from typing import List, Dict, Optional
from database.models import User, Contact, Prompt, DirectChat


class PromptBuilder:

    # === BUSINESS MODE ===
    BUSINESS_BASE = """Ты — {owner_name}. Ты отвечаешь от имени этого человека в Telegram.
НИКОГДА не упоминай, что ты ИИ, бот или ассистент. Ты — реальный человек.

=== ТВОЙ СТИЛЬ ===
{style_prompt}

=== О ТЕБЕ ===
{global_knowledge}

=== О СОБЕСЕДНИКЕ ===
Имя: {contact_name}
Отношения: {relationship}
{contact_notes}

=== ПРАВИЛА ===
- Отвечай естественно, как реальный человек
- Используй тон и стиль, описанный выше
- Не выдумывай факты, которых нет в контексте
- Если не знаешь что ответить — ответь нейтрально, но естественно
- Длина ответа: 1-3 предложения (как в обычном чате)
"""

    # === DIRECT MODE ===
    DIRECT_BASE = """Ты — AI-ассистент пользователя в Telegram.

=== ТВОЯ РОЛЬ ===
{persona_description}

=== СТИЛЬ ОБЩЕНИЯ ===
{style_prompt}

=== О ПОЛЬЗОВАТЕЛЕ ===
{user_knowledge}

=== ПРАВИЛА ===
- Общайся естественно, дружелюбно
- Помогай с вопросами, советами, разговорами
- Не притворяйся человеком — ты AI, и это нормально
- Будь честным о своих возможностях
- Если не знаешь — скажи честно
"""

    @staticmethod
    def build_business_prompt(user: User, contact: Optional[Contact] = None, 
                              prompt: Optional[Prompt] = None) -> str:
        style_prompt = user.custom_prompt or (prompt.system_prompt if prompt else "Отвечай естественно и дружелюбно.")

        knowledge = user.global_knowledge or {}
        knowledge_str = "\n".join([f"- {k}: {v}" for k, v in knowledge.items()]) or "Нет дополнительной информации."

        contact_name = contact.first_name or contact.username or "Собеседник" if contact else "Собеседник"
        relationship = contact.relationship_type or "неизвестно" if contact else "неизвестно"
        notes = f"Заметки: {contact.notes}" if contact and contact.notes else ""

        if contact and contact.extracted_style:
            style_data = contact.extracted_style
            style_notes = f"\nИзвлечённый стиль общения: {style_data.get('tone', 'неизвестно')}"
        else:
            style_notes = ""

        owner_name = user.first_name or "Пользователь"

        return PromptBuilder.BUSINESS_BASE.format(
            owner_name=owner_name,
            style_prompt=style_prompt + style_notes,
            global_knowledge=knowledge_str,
            contact_name=contact_name,
            relationship=relationship,
            contact_notes=notes
        )

    @staticmethod
    def build_direct_prompt(user: User, chat: DirectChat, prompt: Optional[Prompt] = None) -> str:
        style_prompt = chat.system_prompt or user.custom_prompt or (prompt.system_prompt if prompt else "Дружелюбный, полезный ассистент.")

        persona = chat.persona_description or "Универсальный AI-ассистент"

        knowledge = user.global_knowledge or {}
        knowledge_str = "\n".join([f"- {k}: {v}" for k, v in knowledge.items()]) or "Нет информации о пользователе."

        return PromptBuilder.DIRECT_BASE.format(
            persona_description=persona,
            style_prompt=style_prompt,
            user_knowledge=knowledge_str
        )

    @staticmethod
    def build_messages(history: List[Dict], new_message: str) -> List[Dict]:
        messages = []

        for msg in history:
            role = "assistant" if msg["sender_type"] in ["owner", "bot"] else "user"
            messages.append({"role": role, "content": msg["text"]})

        messages.append({"role": "user", "content": new_message})
        return messages
