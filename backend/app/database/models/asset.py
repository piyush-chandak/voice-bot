from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, TimeStampedModelMixin


class Asset(Base, TimeStampedModelMixin):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="operational", nullable=False)

    # Relationships
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="asset")
