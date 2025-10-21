# models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from bases.model import Base


class ApiUsage(Base):
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"))
    path = Column(String)
    method = Column(String)
    status_code = Column(Integer)
    duration = Column(Float)
    timestamp = Column(DateTime, default=datetime.now)

    client = relationship("Client", back_populates="usages")

