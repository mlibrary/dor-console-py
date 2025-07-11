from pathlib import Path
from faker import Faker
import json
import random
from uuid import uuid4
from datetime import datetime, timedelta
import hashlib

from dor.config import config
from dor.models.checksum import Checksum
from dor.models.collection import Collection
from dor.models.premis_event import PremisEvent
from dor.utils import fetch, create_uuid_from_string, extract_identifier
from dor.models.intellectual_object import CurrentRevision, IntellectualObject
from dor.models.object_file import ObjectFile

fake = Faker()

def build_collection(collection_data: dict, collection_type: str):
    identifier, alternate_identifier = extract_identifier(collection_data['@id'])
    collection = Collection(
        identifier=identifier,
        alternate_identifiers=alternate_identifier,
        type=collection_type,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        title=collection_data['label'],
        description=collection_data['attribution']
    )
    return collection


def build_intellectual_objects(collid: str, manifest_data: dict, object_type: str):
    intellectual_objects = []

    identifier, alternate_identifier = extract_identifier(manifest_data['@id'])

    config.console.print(f":stuck_out_tongue_closed_eyes: processing {alternate_identifier}")

    bin_identifier = identifier
    intellectual_object = IntellectualObject(
        bin_identifier=bin_identifier,
        identifier=identifier,
        alternate_identifiers=alternate_identifier,
        type=object_type,
        revision_number=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        title=manifest_data['label']
    )
    intellectual_object.revision = CurrentRevision(
        revision_number=intellectual_object.revision_number,
        intellectual_object=intellectual_object,
        intellectual_object_identifier=intellectual_object.identifier
    )
    intellectual_object.object_files.extend(build_object_files_for_intellectual_object(intellectual_object))
    intellectual_object.premis_events.append(PremisEvent(
        identifier=uuid4(),
        type="ingestion start",
        date_time=(datetime.now() - timedelta(seconds=8600)),
        detail=fake.catch_phrase(),
        outcome=fake.ipv6()
    ))
    intellectual_object.premis_events.append(PremisEvent(
        identifier=uuid4(),
        type="ingestion end",
        date_time=datetime.now(),
        detail=fake.catch_phrase(),
        outcome=fake.ipv6()
    ))

    intellectual_objects.append(intellectual_object)


    canvases = manifest_data['sequences'][0]['canvases']
    for canvas in canvases:

        # canvas ids are so weird
        canvas_id = canvas['@id'].split('/')[-3]
        identifier, alternate_identifier = extract_identifier(canvas_id)
        config.console.print(f":star2: processing {alternate_identifier}")
        intellectual_object = IntellectualObject(
            bin_identifier=bin_identifier,
            identifier=identifier,
            alternate_identifiers=alternate_identifier,
            type="types:fileset",
            revision_number=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            title=manifest_data['label']
        )
        intellectual_object.revision = CurrentRevision(
            revision_number=intellectual_object.revision_number,
            intellectual_object=intellectual_object,
            intellectual_object_identifier=intellectual_object.identifier
        )

        intellectual_object.object_files.extend(
            build_object_files_for_canvas(intellectual_object, canvas))
    
        intellectual_object.premis_events.append(PremisEvent(
            identifier=uuid4(),
            type="ingestion start",
            date_time=(datetime.now() - timedelta(seconds=8600)),
            detail=fake.catch_phrase(),
            outcome=fake.ipv6()
        ))
        intellectual_object.premis_events.append(PremisEvent(
            identifier=uuid4(),
            type="ingestion end",
            date_time=datetime.now(),
            detail=fake.catch_phrase(),
            outcome=fake.ipv6()
        ))

        intellectual_objects.append(intellectual_object)

    return intellectual_objects


def build_object_files_for_intellectual_object(intellectual_object: IntellectualObject):
    object_files = []
    identifier = intellectual_object.identifier
    for file_identifier, file_format, file_function in [
        (f"{identifier}/descriptor/{identifier}.{intellectual_object.type}.mets2.xml", "application/xml", "function:descriptor"),
        (f"{identifier}/metadata/{identifier}.function:source.json", "application/json", "function:source"),
        (f"{identifier}/metadata/{identifier}.function:service.json", "application/json", "function:service"),
        (f"{identifier}/metadata/{identifier}.function:event.json", "application/xml", "function:event"),
        (f"{identifier}/metadata/{identifier}.function:provenance.json", "application/xml", "function:provenance"),
    ]:
        
        digest = fake.sha256(raw_output=True)
        object_file = ObjectFile(
            identifier=file_identifier,
            file_format=file_format,
            file_function=file_function,
            size=fake.random_int(min=600),
            digest=digest,
            revision_number=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_fixity_check=datetime.now()
        )

        checksum = Checksum(
            algorithm="sha256",
            digest=digest,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        object_file.checksums.append(checksum)

        object_file.premis_events.append(PremisEvent(
            identifier=uuid4(),
            type="virus check",
            date_time=(datetime.now() - timedelta(seconds=8600)),
            detail=fake.catch_phrase(),
            outcome=fake.ipv6()
        ))
        object_file.premis_events.append(PremisEvent(
            identifier=uuid4(),
            type="accession",
            date_time=datetime.now(),
            detail=fake.catch_phrase(),
            outcome=fake.ipv6()
        ))

        object_files.append(object_file)

    return object_files

EXTENSIONS = {
    'image/jp2': 'jp2',
    'image/tiff': 'tif'
}

def build_object_files_for_canvas(intellectual_object: IntellectualObject, canvas: dict):
    object_files = []

    object_identifier = intellectual_object.identifier
    resource = canvas['images'][0]['resource']
    resource_id = Path(resource['service']['@id']).name
    mimetype = resource['format']
    ext = EXTENSIONS[mimetype]

    m_fn = resource_id.split(':')[-1]

    possibles = []
    possibles.append((f"{object_identifier}/descriptor/{object_identifier}.types:fileset.mets2.xml",
                     "application/xml", "function:descriptor"))

    function = 'function:source' if mimetype == 'image/tiff' else 'function:service'

    file_identifier = f"{object_identifier}/data/{m_fn}.{function}.format:image.{ext}"
    possibles.append(( file_identifier, mimetype, function ))

    metadata_file_identifier = f"{object_identifier}/metadata/{m_fn}.{function}.format:image.function:technical.mix.xml"
    possibles.append((metadata_file_identifier, "application/xml", "function:technical"))

    event_file_identifier = f"{object_identifier}/metadata/{m_fn}.{function}.format:image.function:event.premis.xml"
    possibles.append((event_file_identifier, "application/xml", "function:event"))

    if function == 'function:service':
        file_identifier = f"{object_identifier}/data/{m_fn}.function:source.format:image.tif"
        possibles.append((file_identifier, "image/tiff", 'function:source'))

        metadata_file_identifier = f"{object_identifier}/metadata/{m_fn}.function:source.format:image.function:technical.mix.xml"
        possibles.append((metadata_file_identifier, "application/xml", "function:technical"))
        
        event_file_identifier = f"{object_identifier}/metadata/{m_fn}.function:source.format:image.function:event.premis.xml"
        possibles.append((event_file_identifier, "application/xml", "function:event"))
    
    for file_identifier, file_format, file_function in possibles:
        digest = fake.sha256(raw_output=True)
        object_file = ObjectFile(
            identifier=file_identifier,
            file_format=file_format,
            file_function=file_function,
            size=fake.random_int(min=600),
            digest=digest,
            revision_number=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_fixity_check=datetime.now()
        )

        checksum = Checksum(
            algorithm="sha256",
            digest=digest,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        object_file.checksums.append(checksum)
        object_files.append(object_file)

    return object_files