import uuid
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DECIMAL, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base

class SMSProvider(Base):
    __tablename__ = "sms_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    adapter_type = Column(String(50), nullable=False)
    config = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    balance = Column(DECIMAL(12, 2), default=0.0)
    priority = Column(Integer, default=1)
    sender_number = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class RoutingRule(Base):
    __tablename__ = "routing_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False)
    message_type = Column(String(50), default="info")
    operator = Column(String(50), default="all")
    provider_id = Column(Integer, ForeignKey("sms_providers.id", ondelete="CASCADE"))
    priority = Column(Integer, default=1)
    weight = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)

class SMSMessage(Base):
    __tablename__ = "sms_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_number = Column(String(20))
    recipient_number = Column(String(20), nullable=False, index=True)
    body = Column(Text, nullable=False)
    provider_id = Column(Integer, ForeignKey("sms_providers.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(30), default="queued")
    message_type = Column(String(20), default="info")
    remote_message_id = Column(String(100), nullable=True)
    retry_count = Column(Integer, default=0)
    cost = Column(DECIMAL(8, 2), default=0.0)
    created_at = Column(DateTime, server_default=func.now())

class RecipientList(Base):
    __tablename__ = "recipient_lists"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    list_type = Column(String(10), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())