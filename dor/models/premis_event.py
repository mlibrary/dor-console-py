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
    identifier: Mapped[str] = mapped_column(String, unique=True)
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
    file_set_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_file_set.id"), nullable=True, index=True
    )

    intellectual_object: Mapped["IntellectualObject"] = relationship(
        back_populates="premis_events")
    file_set: Mapped["FileSet"] = relationship(back_populates="premis_events")
    object_file: Mapped["ObjectFile"] = relationship(
        back_populates="premis_events")
