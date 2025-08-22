from datetime import datetime
from typing import List
import uuid

from sqlalchemy import ARRAY, Column, DateTime, ForeignKey, Integer, LargeBinary, String, Table, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableList

from dor.adapters.sqlalchemy import Base

# NOTE
# Doubtful that the implementation will use a M2M
# relationship betwen collections and objects --- 
# collections MAY natively live in the database
# (as they are managed and not part of the ingest workflow)
# and the catalog is a R/O view into the depot.

collection_object_table = Table(
    "catalog_collection_object_membership",
    Base.metadata,
    Column("intellectual_object_id", ForeignKey(
        "catalog_intellectual_object.id", ondelete="CASCADE"), primary_key=True),
    Column("collection_id", ForeignKey(
        "catalog_collection.id", ondelete="CASCADE"), primary_key=True),
)

class Collection(Base):
    __tablename__ = "catalog_collection"
    id: Mapped[int] = mapped_column(primary_key=True)
    identifier: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, index=True)
    alternate_identifiers: Mapped[str] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    title: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)

    objects: Mapped[List["IntellectualObject"]] = relationship(
        secondary=collection_object_table, back_populates="collections",
        cascade="all, delete"
    )
