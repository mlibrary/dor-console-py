from datetime import datetime
from typing import List
import uuid

from sqlalchemy import ARRAY, Column, DateTime, ForeignKey, Integer, LargeBinary, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableList

from dor.adapters.sqlalchemy import Base


class ObjectFile(Base):
    __tablename__ = "catalog_object_file"
    id: Mapped[int] = mapped_column(primary_key=True)
    identifier: Mapped[str] = mapped_column(String)
    # identifier: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True)
    file_format: Mapped[str] = mapped_column(String, index=True)
    file_function: Mapped[str] = mapped_column(String, index=True)
    size: Mapped[int] = mapped_column(Integer)
    digest: Mapped[bytes] = mapped_column(
        LargeBinary(32), unique=False, nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_fixity_check: Mapped[datetime] = mapped_column(
        DateTime(timezone=True))
    intellectual_object_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_intellectual_object.id", ondelete="CASCADE"), index=True, nullable=True
    )
    fileset_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_fileset.id", ondelete="CASCADE"), index=True, nullable=True
    )

    fileset: Mapped["Fileset"] = relationship(back_populates="object_files")
    intellectual_object: Mapped["IntellectualObject"] = relationship(
        back_populates="object_files")
    premis_events: Mapped[List["PremisEvent"]] = relationship(
        back_populates="object_file")
    checksums: Mapped[List["Checksum"]] = relationship(
        back_populates="object_file")
