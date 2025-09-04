from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dor.adapters.sqlalchemy import Base
# Something weird requiring us to import this
from dor.models.fileset import Fileset


class PremisEvent(Base):
    __tablename__ = "catalog_premis_event"
    id: Mapped[int] = mapped_column(primary_key=True)
    identifier: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True)
    type: Mapped[str] = mapped_column(String)
    date_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    detail: Mapped[str] = mapped_column(String, nullable=True)
    outcome: Mapped[str] = mapped_column(String, nullable=True)
    outcome_detail_note: Mapped[str] = mapped_column(String, nullable=True)
    linking_agent_value: Mapped[str] = mapped_column(String, nullable=True)
    linking_agent_type: Mapped[str] = mapped_column(String, nullable=True)
    linking_agent_role: Mapped[str] = mapped_column(String, nullable=True)
    intellectual_object_id: Mapped[int] = mapped_column(ForeignKey(
        "catalog_intellectual_object.id", ondelete="CASCADE"), nullable=True, index=True)
    object_file_id: Mapped[int] = mapped_column(ForeignKey(
        "catalog_object_file.id", ondelete="CASCADE"), nullable=True, index=True)
    fileset_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_fileset.id", ondelete="CASCADE"), nullable=True, index=True
    )

    intellectual_object: Mapped["IntellectualObject"] = relationship(
        back_populates="premis_events")
    fileset: Mapped["Fileset"] = relationship(back_populates="premis_events")
    object_file: Mapped["ObjectFile"] = relationship(
        back_populates="premis_events")

    def to_dict(self):
        """Converts the SQLAlchemy model instance to a dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
