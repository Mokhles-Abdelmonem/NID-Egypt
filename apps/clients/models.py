from sqlalchemy.orm import relationship

from bases.model import Base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
import secrets


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    api_key = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    usages = relationship("ApiUsage", back_populates="client", cascade="all, delete")

    @staticmethod
    def generate_api_key() -> str:
        # 64-character secure random key
        return secrets.token_urlsafe(48)
