import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200), unique=True)
    plan: Mapped[str] = mapped_column(String(20), default="free")  # free, basic, pro
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # WhatsApp
    waba_id: Mapped[str | None] = mapped_column(String(100))
    whatsapp_phone_number_id: Mapped[str | None] = mapped_column(String(100))
    whatsapp_access_token: Mapped[str | None] = mapped_column(String(500))  # encrypted

    # Messenger
    messenger_page_id: Mapped[str | None] = mapped_column(String(100))
    messenger_access_token: Mapped[str | None] = mapped_column(String(500))  # encrypted

    # Configuración del negocio
    business_name: Mapped[str | None] = mapped_column(String(200))
    business_hours: Mapped[str | None] = mapped_column(String(500))
    business_location: Mapped[str | None] = mapped_column(String(500))
    welcome_message: Mapped[str | None] = mapped_column(String(1000))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    products: Mapped[list["Product"]] = relationship(back_populates="merchant")  # noqa: F821
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="merchant")  # noqa: F821
