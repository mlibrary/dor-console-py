from pathlib import Path
from uuid import uuid4
from datetime import datetime

from faker import Faker

from dor.config import config
from dor.domain import (
    Collection, Checksum, Fileset, IntellectualObject, ObjectFile,
    PremisEvent, LinkingAgent
)
from dor.utils import extract_identifier


fake = Faker()


def build_collection(collection_data: dict, collection_type: str):
    identifier, alternate_identifier = extract_identifier(collection_data['@id'])
    created_at = fake.past_datetime(start_date="-20y")
    collection = Collection(
        identifier=identifier,
        alternate_identifiers=[alternate_identifier],
        type=collection_type,
        created_at=created_at,
        updated_at=created_at,
        title=collection_data['label'],
        description=collection_data['attribution']
    )
    return collection


def make_order_label(label: str, index: int) -> str:
    if label.startswith("Page "):
        new_label = label.replace("Page ", "")
    elif label.startswith("Scan "):
        new_label = label.replace("Scan ", "")
    else:
        new_label = f"#{index + 1}"
    return new_label


def build_intellectual_object(collection: Collection, manifest_data: dict, object_type: str):
    identifier, alternate_identifier = extract_identifier(manifest_data['@id'])

    config.console.print(f":stuck_out_tongue_closed_eyes: processing {alternate_identifier}")

    created_at = fake.past_datetime(start_date="-20y")
    bin_identifier = identifier
    intellectual_object = IntellectualObject(
        bin_identifier=bin_identifier,
        identifier=identifier,
        alternate_identifiers=[alternate_identifier],
        type=object_type,
        revision_number=1,
        created_at=created_at,
        updated_at=created_at,
        title=manifest_data['label'],
        description="",
        premis_events=[],
        filesets=[],
        object_files=[],
        collections=[collection]
    )
    intellectual_object.object_files.extend(
        build_object_files_for_intellectual_object(intellectual_object)
    )
    linking_agent = LinkingAgent(
        value=fake.email(),
        type="",
        role="collection_manager"
    )

    intellectual_object.premis_events.append(PremisEvent(
        identifier=uuid4(),
        type="ingestion start",
        datetime=(created_at + fake.time_delta(end_datetime='-30h')),
        detail=fake.catch_phrase(),
        outcome=fake.ipv6(),
        outcome_detail_note="",
        linking_agent=linking_agent,
    ))
    intellectual_object.premis_events.append(PremisEvent(
        identifier=uuid4(),
        type="ingestion end",
        datetime=created_at,
        detail=fake.catch_phrase(),
        outcome=fake.ipv6(),
        outcome_detail_note="",
        linking_agent=linking_agent
    ))

    canvases = manifest_data['sequences'][0]['canvases']
    for index, canvas in enumerate(canvases):

        # canvas ids are so weird
        canvas_id = canvas['@id'].split('/')[-3]
        identifier, alternate_identifier = extract_identifier(canvas_id)
        config.console.print(f":star2: processing {alternate_identifier}")

        title = alternate_identifier.split(":")[-1]
        created_at = fake.past_datetime(start_date="-20y")
        order_label = make_order_label(canvas["label"], index)

        fileset = Fileset(
            identifier=identifier,
            alternate_identifiers=[alternate_identifier],
            title=title,
            revision_number=1,
            created_at=created_at,
            order_label=order_label,
            object_files=[],
            premis_events=[]
        )

        fileset.object_files.extend(build_object_files_for_canvas(fileset=fileset, canvas=canvas))
        fileset.premis_events.append(PremisEvent(
            identifier=uuid4(),
            type="ingestion start",
            datetime=(created_at - fake.time_delta(end_datetime='-30h')),
            detail=fake.catch_phrase(),
            outcome=fake.ipv6(),
            outcome_detail_note="",
            linking_agent=linking_agent
        ))
        fileset.premis_events.append(PremisEvent(
            identifier=uuid4(),
            type="ingestion end",
            datetime=created_at,
            detail=fake.catch_phrase(),
            outcome=fake.ipv6(),
            outcome_detail_note="",
            linking_agent=linking_agent
        ))

        intellectual_object.filesets.append(fileset)

    return intellectual_object


def build_object_files_for_intellectual_object(intellectual_object: IntellectualObject):
    object_files = []
    identifier = intellectual_object.identifier
    for file_path, file_format, file_function in [
        (f"{identifier}/descriptor/{identifier}.{intellectual_object.type}.mets2.xml", "application/xml", "function:descriptor"),
        (f"{identifier}/metadata/{identifier}.function:source.json", "application/json", "function:source"),
        (f"{identifier}/metadata/{identifier}.function:service.json", "application/json", "function:service"),
        (f"{identifier}/metadata/{identifier}.function:event.json", "application/xml", "function:event"),
        (f"{identifier}/metadata/{identifier}.function:provenance.json", "application/xml", "function:provenance"),
    ]:
        
        digest = fake.sha256(raw_output=True)
        object_file = ObjectFile(
            identifier=uuid4(),
            path=Path(file_path),
            file_format=file_format,
            file_function=file_function,
            size=fake.random_int(min=600),
            digest=digest,
            created_at=intellectual_object.created_at,
            updated_at=intellectual_object.created_at,
            last_fixity_check=datetime.now(),
            checksums=[],
            premis_events=[]
        )

        checksum = Checksum(
            algorithm="sha256",
            digest=digest,
            created_at=intellectual_object.created_at + fake.time_delta(end_datetime="+1h")
        )
        object_file.checksums.append(checksum)

        linking_agent = LinkingAgent(
            value=fake.email(),
            type="",
            role="collection_manager"
        )

        object_file.premis_events.append(PremisEvent(
            identifier=uuid4(),
            type="virus check",
            datetime=(intellectual_object.created_at - fake.time_delta(end_datetime='-30h')),
            detail=fake.catch_phrase(),
            outcome=fake.ipv6(),
            outcome_detail_note="",
            linking_agent=linking_agent
        ))
        object_file.premis_events.append(PremisEvent(
            identifier=uuid4(),
            type="accession",
            datetime=intellectual_object.created_at,
            detail=fake.catch_phrase(),
            outcome=fake.ipv6(),
            outcome_detail_note="",
            linking_agent=linking_agent
        ))

        object_files.append(object_file)

    return object_files

EXTENSIONS = {
    'image/jp2': 'jp2',
    'image/tiff': 'tif'
}

def build_object_files_for_canvas(fileset: Fileset, canvas: dict):
    object_files = []

    object_identifier = fileset.identifier
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

    created_at = fileset.created_at
    for file_identifier, file_format, file_function in possibles:
        digest = fake.sha256(raw_output=True)
        object_file = ObjectFile(
            identifier=uuid4(),
            path=Path(file_identifier),
            file_format=file_format,
            file_function=file_function,
            size=fake.random_int(min=600),
            digest=digest,
            created_at=created_at,
            updated_at=created_at,
            last_fixity_check=datetime.now(),
            checksums=[Checksum(
                algorithm="sha256",
                digest=digest,
                created_at=created_at
            )],
            premis_events=[]
        )
        object_files.append(object_file)

    return object_files