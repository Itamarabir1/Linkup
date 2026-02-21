"""
מודל צ'אט 1:1 – שיחה בין שני משתמשים בלבד.
Conversation = זוג משתמשים (מזוהה יחיד). Message = הודעה בשיחה.
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, func, UniqueConstraint, CheckConstraint, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class Conversation(Base):
    """
    שיחת 1:1 בין שני משתמשים.
    user_id_1 < user_id_2 תמיד – כך הזוג ייחודי בלי כפילות (א־ב = ב־א).
    """
    __tablename__ = "conversations"

    conversation_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id_1 = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    user_id_2 = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id_1", "user_id_2", name="uq_conversation_pair"),
        CheckConstraint("user_id_1 < user_id_2", name="ck_conversation_ordered"),
    )

    user_1 = relationship("User", foreign_keys=[user_id_1])
    user_2 = relationship("User", foreign_keys=[user_id_2])
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self):
        return f"<Conversation(id={self.conversation_id}, users=({self.user_id_1},{self.user_id_2}))>"


class Message(Base):
    """הודעה אחת בתוך שיחת 1:1."""
    __tablename__ = "messages"

    message_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])

    def __repr__(self):
        return f"<Message(id={self.message_id}, conv={self.conversation_id}, sender={self.sender_id})>"


class ChatAnalysis(Base):
    """ניתוח AI של שיחת צ'אט."""
    __tablename__ = "chat_analysis"

    analysis_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    driver_name = Column(Text)
    passenger_name = Column(Text)
    pickup_location = Column(Text)
    meeting_time = Column(Text)
    summary_hebrew = Column(Text)
    analysis_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    conversation = relationship("Conversation", foreign_keys=[conversation_id])

    def __repr__(self):
        return f"<ChatAnalysis(conv={self.conversation_id}, driver={self.driver_name}, passenger={self.passenger_name})>"
