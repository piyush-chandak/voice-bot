from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, TimeStampedModelMixin

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy import PickleType
    # Fallback to PickleType if pgvector library is not installed
    def Vector(dim: int):
        return PickleType


class Memory(Base, TimeStampedModelMixin):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(1536), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="memories")
