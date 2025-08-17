from datetime import datetime
from decimal import Decimal
from typing import List
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from dor.adapters.sqlalchemy import Base
from .collection import collection_object_table


class IntellectualObject(Base):
    """
    Fields for an Intellectual Object:

    bin_identifier
    identifier
    alternate_identifiers
    type
    revision_number
    updated_at
    title
    total_data_size
        - for a content object, the sum of the total_data_size of its filesets
        - for a fileset, the sum of the object files with file_function==function:source
    collection_summary: returns the concatenated collection alternate identifiers

    Methods:
    filesets: returns a list of filesets related to this content object
    premis_events: returns a list of related events
    object_files: returns a list of object file objects for this intellectual object
    """

    __tablename__ = "catalog_intellectual_object"
    id: Mapped[int] = mapped_column(primary_key=True)
    bin_identifier: Mapped[uuid.UUID] = mapped_column(Uuid, unique=False, index=True)
    identifier: Mapped[uuid.UUID] = mapped_column(Uuid, unique=False, index=True)
    alternate_identifiers: Mapped[str] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String, index=True)
    revision_number: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    title: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)

    filesets: Mapped[List["Fileset"]] = relationship(
        back_populates="intellectual_object", cascade="all, delete-orphan", passive_deletes=True
    )

    object_files: Mapped[List["ObjectFile"]] = relationship(back_populates="intellectual_object", lazy="dynamic", cascade="all, delete", passive_deletes=True)
    premis_events: Mapped[List["PremisEvent"]] = relationship(
        back_populates="intellectual_object", cascade="all, delete-orphan", passive_deletes=True)
    revision: Mapped["CurrentRevision"] = relationship(
        back_populates="intellectual_object", uselist=False, cascade="all, delete-orphan", passive_deletes=True)

    collections: Mapped[List["Collection"]] = relationship(
        secondary=collection_object_table, back_populates="objects",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint('identifier', 'revision_number', name='uq_intellectual_object_revision'),
    )

    @property
    def collections_summary(self):
        return '/'.join([ c.alternate_identifiers for c in self.collections ])
    
    @hybrid_property
    def total_data_size(self):
        return sum(
            (f.total_data_size for f in self.filesets),
            start=Decimal("0")
        )


# because CurrentRevision is taken
class CurrentRevision(Base):
    __tablename__ = "catalog_current_revision"
    id: Mapped[int] = mapped_column(primary_key=True)
    revision_number: Mapped[int] = mapped_column(Integer)
    intellectual_object_identifier: Mapped[uuid.UUID] = mapped_column(
        Uuid, unique=True, index=True)
    intellectual_object_id: Mapped[int] = mapped_column(ForeignKey(
        "catalog_intellectual_object.id", ondelete="CASCADE"), unique=False, nullable=True)

    intellectual_object: Mapped["IntellectualObject"] = relationship(
        back_populates="revision", passive_deletes=True)
