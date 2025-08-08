from datetime import datetime
from typing import List
import uuid

from sqlalchemy import ARRAY, Column, DateTime, ForeignKey, Integer, LargeBinary, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableList

from dor.adapters.sqlalchemy import Base


class Checksum(Base):
    __tablename__ = "catalog_checksum"
    id: Mapped[int] = mapped_column(primary_key=True)
    algorithm: Mapped[str] = mapped_column(String)
    # xdatetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    digest: Mapped[bytes] = mapped_column(
        LargeBinary(32), unique=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    object_file_id: Mapped[int] = mapped_column(ForeignKey(
        "catalog_object_file.id", ondelete="CASCADE"), nullable=False, index=True)

    object_file: Mapped["ObjectFile"] = relationship(
        back_populates="checksums", passive_deletes=True)
