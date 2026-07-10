from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from database.models import (
    User, Contact, ChatSession, DirectChat, DirectMessage,
    Message, Prompt, BusinessConnectionLog
)
from typing import Optional, List


async def get_or_create_user(session: AsyncSession, telegram_id: int, **kwargs) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(telegram_id=telegram_id, **kwargs)
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user


async def get_user_by_business_conn(session: AsyncSession, connection_id: str) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.business_connection_id == connection_id)
    )
    return result.scalar_one_or_none()


async def update_business_connection(session: AsyncSession, user_id: int, connection_id: str):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.business_connection_id = connection_id
    user.is_business_connected = True
    await session.commit()


async def get_or_create_contact(session: AsyncSession, owner_id: int, telegram_user_id: int, **kwargs) -> Contact:
    result = await session.execute(
        select(Contact).where(
            and_(Contact.owner_id == owner_id, Contact.telegram_user_id == telegram_user_id)
        )
    )
    contact = result.scalar_one_or_none()

    if not contact:
        contact = Contact(owner_id=owner_id, telegram_user_id=telegram_user_id, **kwargs)
        session.add(contact)
        await session.commit()
        await session.refresh(contact)

    return contact


async def get_or_create_chat_session(session: AsyncSession, owner_id: int, chat_id: int, 
                                     contact_id: Optional[int] = None, session_type: str = "business") -> ChatSession:
    result = await session.execute(
        select(ChatSession).where(
            and_(ChatSession.owner_id == owner_id, ChatSession.chat_id == chat_id)
        )
    )
    session_obj = result.scalar_one_or_none()

    if not session_obj:
        session_obj = ChatSession(
            owner_id=owner_id, 
            chat_id=chat_id, 
            contact_id=contact_id,
            session_type=session_type
        )
        session.add(session_obj)
        await session.commit()
        await session.refresh(session_obj)

    return session_obj


async def get_or_create_direct_chat(session: AsyncSession, user_id: int) -> DirectChat:
    result = await session.execute(
        select(DirectChat).where(
            and_(DirectChat.user_id == user_id, DirectChat.is_active == True)
        )
    )
    chat = result.scalar_one_or_none()

    if not chat:
        chat = DirectChat(user_id=user_id)
        session.add(chat)
        await session.commit()
        await session.refresh(chat)

    return chat


async def get_chat_history(session: AsyncSession, session_id: int, limit: int = 20) -> List[Message]:
    result = await session.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(desc(Message.created_at))
        .limit(limit)
    )
    return list(reversed(result.scalars().all()))


async def get_direct_chat_history(session: AsyncSession, chat_id: int, limit: int = 20) -> List[DirectMessage]:
    result = await session.execute(
        select(DirectMessage)
        .where(DirectMessage.chat_id == chat_id)
        .order_by(desc(DirectMessage.created_at))
        .limit(limit)
    )
    return list(reversed(result.scalars().all()))


async def add_message(session: AsyncSession, session_id: int, sender_type: str, text: str, 
                      contact_id: Optional[int] = None, tokens_input: int = 0, 
                      tokens_output: int = 0, llm_model: str = "") -> Message:
    msg = Message(
        session_id=session_id,
        contact_id=contact_id,
        sender_type=sender_type,
        text=text,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        llm_model=llm_model
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg


async def add_direct_message(session: AsyncSession, chat_id: int, sender_type: str, text: str,
                             tokens_input: int = 0, tokens_output: int = 0, 
                             llm_model: str = "") -> DirectMessage:
    msg = DirectMessage(
        chat_id=chat_id,
        sender_type=sender_type,
        text=text,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        llm_model=llm_model
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg


async def get_prompts(session: AsyncSession, category: Optional[str] = None) -> List[Prompt]:
    query = select(Prompt).where(Prompt.is_active == True)
    if category:
        query = query.where(Prompt.category == category)
    result = await session.execute(query)
    return result.scalars().all()


async def get_prompt_by_id(session: AsyncSession, prompt_id: int) -> Optional[Prompt]:
    result = await session.execute(select(Prompt).where(Prompt.id == prompt_id))
    return result.scalar_one_or_none()


async def update_user_prompt(session: AsyncSession, user_id: int, prompt_id: int):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.chosen_prompt_id = prompt_id
    await session.commit()


async def update_user_knowledge(session: AsyncSession, user_id: int, knowledge: dict):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.global_knowledge = knowledge
    await session.commit()


async def update_contact(session: AsyncSession, contact_id: int, **kwargs):
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one()
    for key, value in kwargs.items():
        setattr(contact, key, value)
    await session.commit()


async def update_direct_chat(session: AsyncSession, chat_id: int, **kwargs):
    result = await session.execute(select(DirectChat).where(DirectChat.id == chat_id))
    chat = result.scalar_one()
    for key, value in kwargs.items():
        setattr(chat, key, value)
    await session.commit()


async def get_user_stats(session: AsyncSession, user_id: int) -> dict:
    contacts_count = await session.execute(
        select(func.count(Contact.id)).where(Contact.owner_id == user_id)
    )
    messages_count = await session.execute(
        select(func.count(Message.id))
        .join(ChatSession)
        .where(ChatSession.owner_id == user_id)
    )
    sessions_count = await session.execute(
        select(func.count(ChatSession.id)).where(ChatSession.owner_id == user_id)
    )
    direct_messages = await session.execute(
        select(func.count(DirectMessage.id))
        .join(DirectChat)
        .where(DirectChat.user_id == user_id)
    )

    return {
        "contacts": contacts_count.scalar(),
        "messages": messages_count.scalar(),
        "sessions": sessions_count.scalar(),
        "direct_messages": direct_messages.scalar()
    }


async def log_business_connection(session: AsyncSession, user_id: int, connection_id: str, 
                                  action: str, details: dict = None):
    log = BusinessConnectionLog(
        user_id=user_id,
        business_connection_id=connection_id,
        action=action,
        details=details or {}
    )
    session.add(log)
    await session.commit()
