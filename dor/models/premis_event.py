from datetime import datetime
from typing import List
import uuid

from sqlalchemy import ARRAY, Column, DateTime, ForeignKey, Integer, LargeBinary, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableList

from dor.adapters.sqlalchemy import Base


class PremisEvent(Base):
    __tablename__ = "catalog_premis_event"
    id: Mapped[int] = mapped_column(primary_key=True)
    # event_identifier
    identifier: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True)
    type: Mapped[str] = mapped_column(String)
    date_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    detail: Mapped[str] = mapped_column(String, nullable=True)
    outcome: Mapped[str] = mapped_column(String, nullable=True)
    outcome_detail_note: Mapped[str] = mapped_column(String, nullable=True)
    linking_agent: Mapped[str] = mapped_column(String, nullable=True)
    linking_agent: Mapped[str] = mapped_column(String, nullable=True)
    # foreign key to file set file
    intellectual_object_id: Mapped[int] = mapped_column(ForeignKey(
        "catalog_intellectual_object.id"), nullable=True, index=True)
    object_file_id: Mapped[int] = mapped_column(ForeignKey(
        "catalog_object_file.id"), nullable=True, index=True)

    intellectual_object: Mapped["IntellectualObject"] = relationship(
        back_populates="premis_events")
    object_file: Mapped["ObjectFile"] = relationship(
        back_populates="premis_events")
