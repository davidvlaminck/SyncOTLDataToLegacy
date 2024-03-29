from datetime import datetime
from typing import Optional, Sequence, Union, List

from pydantic import BaseModel, Field


class Link(BaseModel):
    href: Optional[str] = None
    rel: Optional[str] = None


class EventContextDTO(BaseModel):
    links: Optional[Sequence[Link]] = None
    uuid: Optional[str] = None
    omschrijving: Optional[str] = None
    createdOn: Optional[datetime] = None
    modifiedOn: Optional[datetime] = None


class ResourceRefDTO(BaseModel):
    links: Optional[Sequence[Link]] = None
    uuid: Optional[str] = None


class AggregateIdObject(BaseModel):
    _type: Optional[str] = None
    uuid: Optional[str] = None


class AtomValueObject(BaseModel):
    type: str = Field(alias='_type')
    typeVersion: str = Field(alias='_typeVersion')
    contextId: Optional[str] = None
    from_: Optional[object] = Field(alias='from')
    to: Optional[object] = None
    aggregateId: Optional[AggregateIdObject] = None


class ContentObject(BaseModel):
    type: Optional[str] = None
    value: Optional[AtomValueObject] = None


class EntryObject(BaseModel):
    content: Optional[ContentObject]
    id: Optional[str]
    links: Optional[Sequence[Link]] = None
    updated: Optional[datetime] = None


class FeedProxyContentValue(BaseModel):
    event_type: Optional[str] = Field(alias='event-type')
    asset_type: Optional[str] = Field(alias='asset-type')
    event_id: Optional[str] = Field(alias='event-id')
    context_id: Optional[str] = Field(alias='context-id', default=None)

    uuids: Optional[Sequence[str]] = None
    aim_ids: Optional[Sequence[str]] = Field(alias='aim-ids')


class FeedProxyContent(BaseModel):
    value: FeedProxyContentValue


class ProxyEntryObject(BaseModel):
    id: str
    type: Optional[str] = Field(alias='_type')
    updated: datetime
    content: Optional[FeedProxyContent] = None


class FeedProxyPage(BaseModel):
    id: str
    base: Optional[str] = None
    title: Optional[str] = None
    updated: Optional[datetime] = None
    links: Optional[Sequence[Link]] = None
    entries: Optional[Sequence[ProxyEntryObject]] = None


class FeedPage(BaseModel):
    id: str
    base: Optional[str] = None
    title: Optional[str] = None
    updated: Optional[datetime] = None
    links: Optional[Sequence[Link]] = None
    entries: Optional[Sequence[EntryObject]] = None


class EigenschapTypedValueDTO(BaseModel):
    type: Optional[str] = Field(alias='_type')
    value: Optional[Union[object, Sequence[object]]] = None


class KenmerkEigenschapValueUpdateDTO(BaseModel):
    eigenschap: ResourceRefDTO = None
    kenmerkType: ResourceRefDTO = None
    typedValue: EigenschapTypedValueDTO = None


class DatatypeTypeDTO(BaseModel):
    type: Optional[str] = Field(alias='_type')


class EigenschapTypeDTO(BaseModel):
    actief: Optional[bool] = None
    links: Optional[Sequence[Link]] = None
    uuid: Optional[str] = None
    kardinaliteitMin: Optional[int] = None
    kardinaliteitMax: Optional[int] = None
    uri: Optional[str] = None
    definitie: Optional[str] = None
    naam: Optional[str] = None
    type: Optional[DatatypeTypeDTO] = None


class EigenschapTypeDTOType(BaseModel):
    datatype: Optional[EigenschapTypeDTO] = None
    type: Optional[str] = Field(alias='_type')


class EigenschapDTO(BaseModel):
    actief: Optional[bool] = None
    links: Optional[Sequence[Link]] = None
    uuid: Optional[str] = None
    kardinaliteitMin: Optional[int] = None
    kardinaliteitMax: Optional[int] = None
    uri: Optional[str] = None
    naam: Optional[str] = None
    type: Optional[EigenschapTypeDTOType] = None


class KenmerkTypeDTO(BaseModel):
    actief: Optional[bool] = None
    links: Optional[Sequence[Link]] = None
    uuid: Optional[str] = None
    uri: Optional[str] = None
    naam: Optional[str] = None


class KenmerkEigenschapValueDTO(BaseModel):
    eigenschap: EigenschapDTO = None
    kenmerkType: KenmerkTypeDTO = None
    typedValue: EigenschapTypedValueDTO = None


class KenmerkEigenschapValueDTOList(BaseModel):
    data: Optional[List[KenmerkEigenschapValueDTO]] = None


class ListUpdateDTOKenmerkEigenschapValueUpdateDTO(BaseModel):
    data: Optional[Sequence[KenmerkEigenschapValueUpdateDTO]] = None


class EigenschapDTOList(BaseModel):
    data: Optional[Sequence[EigenschapDTO]] = None
