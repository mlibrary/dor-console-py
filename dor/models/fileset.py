from datetime import datetime
from typing import List

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dor.adapters.sqlalchemy import Base
from dor.models.object_file import ObjectFile


class FileSet(Base):
    __tablename__ = "catalog_file_set"
    id: Mapped[int] = mapped_column(primary_key=True)
    identifier: Mapped[str] = mapped_column(String, unique=False, index=True)
    alternate_identifiers: Mapped[str] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String, index=True)
    revision_number: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    intellectual_object_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_intellectual_object.id"), nullable=True, index=True
    )

    intellectual_object: Mapped["IntellectualObject"] = relationship(back_populates="file_sets")
    object_files: Mapped[List[ObjectFile]] = relationship(back_populates="file_set", lazy="dynamic")
    premis_events: Mapped[List["PremisEvent"]] = relationship(back_populates="file_set")

    __table_args__ = (
        UniqueConstraint('identifier', 'revision_number', name='uq_fileset_revision'),
    )

