from abc import ABC
from datetime import UTC
from uuid import UUID

import sqlalchemy

from dor.domain import PremisEventConnected, LinkingAgent
from dor.models.intellectual_object import (
    CurrentRevision as CurrentRevisionModel,
    IntellectualObject as IntellectualObjectModel
)
from dor.models.premis_event import PremisEvent as PremisEventModel


class PremisEventRepository(ABC):

    def add(self, event: PremisEventConnected) -> None:
        raise NotImplementedError

    def get(self, identifier: UUID) -> PremisEventConnected | None:
        raise NotImplementedError


class MemoryPremisEventRepository(PremisEventRepository):

    def __init__(self) -> None:
        self.events: list[PremisEventConnected] = []

    def add(self, event: PremisEventConnected) -> None:
        self.events.append(event)

    def get(self, identifier: UUID) -> PremisEventConnected | None:
        for event in self.events:
            if event.identifier == identifier:
                return event
        return None


class SqlalchemyPremisEventRepository(PremisEventRepository):

    def __init__(self, session):
        self.session = session

    def _get_latest_object(self, identifier: UUID) -> IntellectualObjectModel | None:
        query = sqlalchemy.select(IntellectualObjectModel) \
            .join(CurrentRevisionModel) \
            .where(IntellectualObjectModel.identifier == identifier)
        try:
            return self.session.scalars(query).one()
        except sqlalchemy.exc.NoResultFound:
            return None

    @staticmethod
    def model_to_premis_event_connected(model: PremisEventModel) -> PremisEventConnected:
        intellectual_object_identifier = model.intellectual_object.identifier \
            if model.intellectual_object else None

        return PremisEventConnected(
            identifier=model.identifier,
            type=model.type,
            datetime=model.date_time.replace(tzinfo=UTC),
            detail=model.detail,
            outcome=model.outcome,
            outcome_detail_note=model.outcome_detail_note,
            linking_agent=LinkingAgent(
                value=model.linking_agent_value,
                type=model.linking_agent_type,
                role=model.linking_agent_role
            ),
            intellectual_object_identifier=intellectual_object_identifier
        )

    def add(self, event: PremisEventConnected) -> None:
        event_model = PremisEventModel(
            identifier=event.identifier,
            type=event.type,
            date_time=event.datetime,
            detail=event.detail,
            outcome=event.outcome,
            outcome_detail_note=event.outcome_detail_note,
            linking_agent_value=event.linking_agent.value,
            linking_agent_type=event.linking_agent.type,
            linking_agent_role=event.linking_agent.role
        )

        if event.intellectual_object_identifier:
            related_object = self._get_latest_object(event.intellectual_object_identifier)
            event_model.intellectual_object = related_object

        self.session.add(event_model)

    def get(self, identifier: UUID) -> PremisEventConnected | None:
        query = sqlalchemy.select(PremisEventModel) \
            .where(PremisEventModel.identifier == identifier)
        try:
            result = self.session.scalars(query).one()
        except sqlalchemy.exc.NoResultFound:
            return None
        
        event = SqlalchemyPremisEventRepository.model_to_premis_event_connected(result)
        return event
