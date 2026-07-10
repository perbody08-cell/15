from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, BigInteger, Float
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))

    # Business Mode
    business_connection_id = Column(String(255), unique=True)
    is_business_connected = Column(Boolean, default=False)

    # Direct Mode (общение с ботом)
    direct_mode_enabled = Column(Boolean, default=True)
    direct_persona = Column(Text)  # Персона для прямого общения

    # Настройки
    chosen_prompt_id = Column(Integer, ForeignKey("prompts.id"), default=1)
    custom_prompt = Column(Text)
    global_knowledge = Column(JSON, default=dict)

    # LLM
    llm_provider = Column(String(50), default="mock")
    llm_api_key = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contacts = relationship("Contact", back_populates="owner", lazy="selectin")
    chat_sessions = relationship("ChatSession", back_populates="owner", lazy="selectin")
    direct_chats = relationship("DirectChat", back_populates="user", lazy="selectin")
    prompt = relationship("Prompt", lazy="selectin")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    telegram_user_id = Column(BigInteger)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))

    relationship_type = Column(String(50), default="unknown")
    notes = Column(Text)
    extracted_style = Column(JSON, default=dict)

    is_active = Column(Boolean, default=True)
    use_custom_prompt = Column(Boolean, default=False)
    custom_prompt = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="contacts")
    messages = relationship("Message", back_populates="contact", lazy="selectin")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    chat_id = Column(BigInteger, nullable=False)

    session_type = Column(String(20), default="business")  # business, direct
    is_active = Column(Boolean, default=True)
    last_message_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="chat_sessions")
    messages = relationship("Message", back_populates="session", lazy="selectin")


class DirectChat(Base):
    """Прямое общение пользователя с ботом (не Business)"""
    __tablename__ = "direct_chats"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Настройки персоны для этого чата
    persona_name = Column(String(100), default="Помощник")
    persona_description = Column(Text)
    system_prompt = Column(Text)

    # Контекст
    context_summary = Column(Text)  # Сводка предыдущих разговоров

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="direct_chats")
    messages = relationship("DirectMessage", back_populates="chat", lazy="selectin")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"))

    sender_type = Column(String(20), nullable=False)  # owner, contact, bot
    text = Column(Text)

    tokens_input = Column(Integer)
    tokens_output = Column(Integer)
    llm_model = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
    contact = relationship("Contact", back_populates="messages")


class DirectMessage(Base):
    """Сообщения в прямом чате с ботом"""
    __tablename__ = "direct_messages"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("direct_chats.id"), nullable=False)

    sender_type = Column(String(20), nullable=False)  # user, bot
    text = Column(Text)

    tokens_input = Column(Integer)
    tokens_output = Column(Integer)
    llm_model = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship("DirectChat", back_populates="messages")


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    system_prompt = Column(Text, nullable=False)
    category = Column(String(50), default="business")  # business, direct, universal
    is_custom = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="prompt")


class BusinessConnectionLog(Base):
    __tablename__ = "business_connection_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    business_connection_id = Column(String(255))
    action = Column(String(50))
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
