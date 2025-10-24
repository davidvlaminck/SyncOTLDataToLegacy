import json
from datetime import datetime
from typing import Generator, Iterator

from requests import Response

from API.AbstractRequester import AbstractRequester
from Domain.EMInfraDomain import FeedProxyPage, EventContextDTO, InstallatieDTO, InstallatieUpdateDTO, LocatieDTO, \
    LocatieKenmerkDTO, LocatieKenmerkUpdateLocatieDTO, LocatieRelatieUpdateDTO, AssetRefDTO, \
    KenmerkEigenschapValueDTOList, ListUpdateDTOKenmerkEigenschapValueUpdateDTO, KenmerkEigenschapValueUpdateDTO, \
    EigenschapTypedValueDTO, QueryDTO, SelectionDTO, ExpressionDTO, TermDTO, EventContextDTOList, EventDTOList, EventDTO
from Domain.ZoekParameterOTL import ZoekParameterOTL


class EMInfraRestClient:
    kenmerk_uuids = {
        'lgc:installatie#VPLMast': 'bfd35cc8-a787-4517-bcb3-895126a8414c',
        'lgc:installatie#VPConsole': 'd6a0792e-531f-46cb-ba85-8492007d5ea0',
        'lgc:installatie#VPBevestig': '2588c15f-b84d-41bf-a2c9-ad2c0376960b',
        'lgc:installatie#VVOP': 'dfb4ca9b-8744-4088-bce9-67771a30d6bd'
    }

    def __init__(self, requester: AbstractRequester):
        self.requester = requester
        self.requester.first_part_url += 'eminfra/'

    def get_installatie_by_id(self, id: str) -> InstallatieDTO:
        response = self.requester.get(
            url=f'core/api/installaties/{id}')
        if response.status_code != 200:
            print(response)
            raise RuntimeError(response.content.decode())

        response_string = response.content.decode()
        return InstallatieDTO.model_validate_json(response_string)

    def put_installatie_by_id(self, id: str, changed_installatie: InstallatieUpdateDTO) -> bool:
        response = self.requester.put(
            url=f'core/api/installaties/{id}', json=changed_installatie.dict())
        if response.status_code != 202:
            print(response)
            raise RuntimeError(response.content.decode())

        return True

    @classmethod
    def create_installatie_update_from_installatie(cls, installatie: InstallatieDTO) -> InstallatieUpdateDTO:
        return InstallatieUpdateDTO(
            actief=installatie.actief,
            commentaar=installatie.commentaar,
            toestand=installatie.toestand,
            naam=installatie.naam
        )

    def get_locatie_by_installatie_id(self, id: str) -> LocatieKenmerkDTO:
        response = self.requester.get(
            url=f'core/api/installaties/{id}/kenmerken/80052ed4-2f91-400c-8cba-57624653db11')
        if response.status_code != 200:
            print(response)
            raise RuntimeError(response.content.decode())

        response_string = response.content.decode()
        return LocatieKenmerkDTO.model_validate_json(response_string)

    @classmethod
    def create_locatie_kenmerk_update_from_locatie_kenmerk(cls, locatie: LocatieKenmerkDTO
                                                           ) -> LocatieKenmerkUpdateLocatieDTO:
        if locatie is None:
            return LocatieKenmerkUpdateLocatieDTO()
        locatie_kenmerk_update = LocatieKenmerkUpdateLocatieDTO(locatie=locatie.locatie)
        locatie_kenmerk_update.locatie.type = 'punt'
        if locatie.relatie is None or locatie.relatie.asset is None:
            return locatie_kenmerk_update

        locatie_kenmerk_update.relatie = LocatieRelatieUpdateDTO(
            asset=AssetRefDTO(uuid=locatie.relatie.asset.uuid))
        return locatie_kenmerk_update

    def put_locatie_kenmerk_update_by_id(self, id: str, locatie_kenmerk_update: LocatieKenmerkUpdateLocatieDTO) -> bool:
        response = self.requester.put(
            url=f'core/api/installaties/{id}/kenmerken/80052ed4-2f91-400c-8cba-57624653db11',
            json=locatie_kenmerk_update.model_dump(by_alias=True))
        if response.status_code != 202:
            print(response)
            raise RuntimeError(response.content.decode())

        return True

    def get_objects_from_oslo_search_endpoint_using_iterator(
            self, resource: str,
            cursor: str | None = None,
            size: int = 100,
            filter_dict: dict = None) -> Generator[dict, None, None]:
        while True:
            response = self.get_objects_from_oslo_search_endpoint(
                resource=resource, cursor=cursor, size=size, filter_dict=filter_dict)

            decoded_string = response.content.decode()
            graph = json.loads(decoded_string)
            headers = dict(response.headers)

            yield from graph['@graph']
            if 'em-paging-next-cursor' not in headers:
                break
            cursor = headers['em-paging-next-cursor']

    def get_objects_from_oslo_search_endpoint(self, resource: str,
                                              cursor: str | None = None,
                                              size: int = 100,
                                              filter_dict: dict = None) -> Response:
        url = f'core/api/otl/{resource}/search'
        otl_zoekparameter = ZoekParameterOTL(size=size, from_cursor=cursor, filter_dict=filter_dict)

        if resource == 'agents':
            otl_zoekparameter.expansion_field_list = ['contactInfo']

        json_data = otl_zoekparameter.to_dict()

        return self.requester.post(url=url, json=json_data)

    def get_current_feed_page(self) -> FeedProxyPage:
        response = self.requester.get(
            url='feedproxy/feed/assets')
        if response.status_code != 200:
            print(response)
            raise RuntimeError(response.content.decode())

        response_string = response.content.decode()
        return FeedProxyPage.model_validate_json(response_string)

    def get_feed_page_by_number(self, page_number: str) -> FeedProxyPage:
        response = self.requester.get(
            url=f'feedproxy/feed/assets/{page_number}/100')
        if response.status_code != 200:
            print(response)
            raise RuntimeError(response.content.decode())

        response_string = response.content.decode()
        return FeedProxyPage.model_validate_json(response_string)

    def get_event_context_by_uuid(self, uuid: str) -> EventContextDTO:
        response = self.requester.get(
            url=f'core/api/eventcontexts/{uuid}')
        if response.status_code != 200:
            print(response)
            raise RuntimeError(response.content.decode())

        response_string = response.content.decode()
        return EventContextDTO.model_validate_json(response_string)

    def get_eigenschapwaarden_by_id(self, id: str) -> KenmerkEigenschapValueDTOList:
        response = self.requester.get(
            url=f'core/api/installaties/{id}/eigenschapwaarden')
        if response.status_code != 200:
            print(response)
            raise ProcessLookupError(response.content.decode("utf-8"))

        response_string = response.content.decode("utf-8")
        eigenschap_waarden = KenmerkEigenschapValueDTOList.parse_raw(response_string)

        return eigenschap_waarden

    def patch_eigenschapwaarden(self, id: str, update_dto: ListUpdateDTOKenmerkEigenschapValueUpdateDTO):
        if len(update_dto.data) == 0:
            return

        json_data = update_dto.dict(by_alias=True)
        response = self.requester.patch(
            url=f'core/api/installaties/{id}/eigenschapwaarden', json=json_data)
        if response.status_code != 202:
            print(response)
            raise ProcessLookupError(response.content.decode())

    @classmethod
    def create_update_eigenschappen_from_update_dict(cls, update_dict: dict, short_uri: str
                                                     ) -> ListUpdateDTOKenmerkEigenschapValueUpdateDTO:
        # zie get_attribute_dict_from_legacy_drager
        update_dto = ListUpdateDTOKenmerkEigenschapValueUpdateDTO(data=[])

        if not update_dict:
            return update_dto

        armlengte = update_dict.get('armlengte')
        if armlengte == 'niet-van-toepassing':
            armlengte = 'niet van toepassing'
            update_dict['armlengte'] = armlengte

        kenmerk_uuid = cls.kenmerk_uuids[short_uri]

        for key, value in update_dict.items():
            eigenschap_uuid = cls.get_eigenschap_uuid(key=key, short_uri=short_uri)
            type_value = cls.get_type_from_value(value)
            if type_value == 'list':
                typed_value = [EigenschapTypedValueDTO(value=el, _type=cls.get_type_from_value(el))
                               for el in value]
                update_dto.data.append(
                    KenmerkEigenschapValueUpdateDTO(
                        eigenschap=AssetRefDTO(uuid=eigenschap_uuid),
                        kenmerkType=AssetRefDTO(uuid=kenmerk_uuid),
                        typedValue=EigenschapTypedValueDTO(value=typed_value, _type='list')
                    )
                )

            else:    
                update_dto.data.append(
                    KenmerkEigenschapValueUpdateDTO(
                        eigenschap=AssetRefDTO(uuid=eigenschap_uuid),
                        kenmerkType=AssetRefDTO(uuid=kenmerk_uuid),
                        typedValue=EigenschapTypedValueDTO(value=value, _type=type_value)
                    )
                )

        return update_dto

    vplmast_eigenschap_uuids = {
        'aantal_armen': '56bca145-b059-4f96-8aa3-8f6e68828f9a',  # vplmast
        'aantal_te_verlichten_rijvakken_LED': 'da9bb59b-d949-42fc-81e4-8f978ec917a6',
        'aantal_verlichtingstoestellen': '568ba32e-847c-496a-be20-5d022897f032',
        'armlengte': '84d8813c-ffe5-4051-8e56-fdb7d58a772a',  # vplmast
        'contractnummer_levering_LED': '6e319c32-8e94-476c-965f-32b93c461d20',
        'datum_installatie_LED': 'ed270590-4b11-421d-b921-36034323a9a9',
        'kleurtemperatuur_LED': 'e0d154ec-1184-41c3-897d-33064fff73f6',
        'LED_verlichting': 'e7ad2d9f-45f3-4e4a-be98-51d71e19c28b',
        'lamp_type': '070149cc-55f4-491f-a034-21e832e3a9e5',
        'drager_buiten_gebruik': '568b3afb-9f5b-4840-ad0f-d7319a3239b7',  # vplmast
        'lichtpunthoogte_tov_rijweg': 'abbe9222-38ea-47f5-ac9b-cc48b77a7d86',
        'lumen_pakket_LED': '218f8269-21eb-445a-9c77-acb3faf6c3ba',
        'merk_en_type_armatuurcontroller_1': 'd9bbd6b8-bbd2-4cd1-93a8-d526711c7626',  # vplmast
        'merk_en_type_armatuurcontroller_2': '470de0fc-5a9f-4f31-ad7a-eb3682946e2b',  # vplmast
        'merk_en_type_armatuurcontroller_3': 'fcf8919f-d4c1-4556-8447-780586989e55',  # vplmast
        'merk_en_type_armatuurcontroller_4': 'cc790306-68b5-4316-82bb-6acf33483b99',  # vplmast
        'overhang_LED': '179d835d-b981-4a72-a93e-08f0c914b448',
        'paalhoogte': '21348b32-e7f0-4b33-bf10-094d47f05ee7',  # vplmast
        'RAL_kleur': '08fa1ccc-6ef8-4f62-bb05-2fba49d9ae1f',  # vplmast
        'serienummer_armatuurcontroller_1': 'f854f1af-a60b-4e53-a7d3-8ccd701bd7cd',  # vplmast
        'serienummer_armatuurcontroller_2': '91288b7a-8a05-4b4b-8924-5372d93db1aa',  # vplmast
        'serienummer_armatuurcontroller_3': 'f4219f6a-80c1-479b-94d2-ddea275038f4',  # vplmast
        'serienummer_armatuurcontroller_4': '4ec160b6-2fa9-4bc5-9b67-b21fdc4fa562',  # vplmast
        'verlichtingsniveau_LED': '79b94e56-1e8a-4b20-a0f7-8fe76e18f568',
        'verlichtingstoestel_merk_en_type': '54ef5679-2b55-441a-8b4c-fbecde2c06f2',
        'verlichtingstoestel_systeemvermogen': '8ea7f7ef-c187-4a68-a92b-6a0ca855ba50',
        'verlichtingstype': '79e547aa-e248-4dff-9c52-30befba43f3d'
    }

    vpconsole_eigenschap_uuids = {
        'aantal_te_verlichten_rijvakken_LED': 'da9bb59b-d949-42fc-81e4-8f978ec917a6',
        'aantal_verlichtingstoestellen': '568ba32e-847c-496a-be20-5d022897f032',
        'contractnummer_levering_LED': '6e319c32-8e94-476c-965f-32b93c461d20',
        'datum_installatie_LED': 'ed270590-4b11-421d-b921-36034323a9a9',
        'kleurtemperatuur_LED': 'e0d154ec-1184-41c3-897d-33064fff73f6',
        'LED_verlichting': 'e7ad2d9f-45f3-4e4a-be98-51d71e19c28b',
        'lamp_type': '070149cc-55f4-491f-a034-21e832e3a9e5',
        'lichtpunthoogte_tov_rijweg': 'abbe9222-38ea-47f5-ac9b-cc48b77a7d86',
        'lumen_pakket_LED': '218f8269-21eb-445a-9c77-acb3faf6c3ba',
        'overhang_LED': '179d835d-b981-4a72-a93e-08f0c914b448',
        'verlichtingsniveau_LED': '79b94e56-1e8a-4b20-a0f7-8fe76e18f568',
        'verlichtingstoestel_merk_en_type': '54ef5679-2b55-441a-8b4c-fbecde2c06f2',
        'verlichtingstoestel_systeemvermogen': '8ea7f7ef-c187-4a68-a92b-6a0ca855ba50',
        'verlichtingstype': '79e547aa-e248-4dff-9c52-30befba43f3d',
        'serienummer_armatuurcontroller_1': 'c8ff119b-c315-4c2e-a5cc-1cf472b80861',
        'drager_buiten_gebruik': 'cccefbc9-621b-4f0b-99f6-4a800e7bbe79',
        'RAL_kleur': 'a83d51f5-c8be-4f63-91e0-13812cc435f8',
    }

    vpbevestig_eigenschap_uuids = {
        'aantal_te_verlichten_rijvakken_LED': 'da9bb59b-d949-42fc-81e4-8f978ec917a6',
        'aantal_verlichtingstoestellen': '568ba32e-847c-496a-be20-5d022897f032',
        'contractnummer_levering_LED': '6e319c32-8e94-476c-965f-32b93c461d20',
        'datum_installatie_LED': 'ed270590-4b11-421d-b921-36034323a9a9',
        'kleurtemperatuur_LED': 'e0d154ec-1184-41c3-897d-33064fff73f6',
        'LED_verlichting': 'e7ad2d9f-45f3-4e4a-be98-51d71e19c28b',
        'lamp_type': '070149cc-55f4-491f-a034-21e832e3a9e5',
        'lichtpunthoogte_tov_rijweg': 'abbe9222-38ea-47f5-ac9b-cc48b77a7d86',
        'lumen_pakket_LED': '218f8269-21eb-445a-9c77-acb3faf6c3ba',
        'overhang_LED': '179d835d-b981-4a72-a93e-08f0c914b448',
        'verlichtingsniveau_LED': '79b94e56-1e8a-4b20-a0f7-8fe76e18f568',
        'verlichtingstoestel_merk_en_type': '54ef5679-2b55-441a-8b4c-fbecde2c06f2',
        'verlichtingstoestel_systeemvermogen': '8ea7f7ef-c187-4a68-a92b-6a0ca855ba50',
        'verlichtingstype': '79e547aa-e248-4dff-9c52-30befba43f3d',
        'serienummer_armatuurcontroller_1': 'c8ff119b-c315-4c2e-a5cc-1cf472b80861',
        'drager_buiten_gebruik': 'bb01b492-1777-4101-9220-2a3f5df853e3',
    }

    @classmethod
    def get_eigenschap_uuid(cls, key, short_uri):
        if short_uri == 'lgc:installatie#VPLMast':
            return cls.vplmast_eigenschap_uuids[key]
        if short_uri == 'lgc:installatie#VPConsole':
            return cls.vpconsole_eigenschap_uuids[key]
        if short_uri == 'lgc:installatie#VPBevestig':
            return cls.vpbevestig_eigenschap_uuids[key]

    @classmethod
    def get_type_from_value(cls, value: object) -> str:
        if value is None:
            return 'text'
        if isinstance(value, list):
            return 'list'
        if isinstance(value, str):
            try:
                dt = datetime.strptime(value, '%Y-%m-%d')
                return 'date'
            except ValueError:
                return 'text'
        if isinstance(value, bool):
            return 'boolean'
        if isinstance(value, (int, float)):
            return 'number'
        raise NotImplementedError(f'no type defined for {value}')

    def get_feed_events_by_eventcontext_id(self, context_id: str, size: int = 10) -> Iterator[EventDTO]:
        search_query_dto = QueryDTO(
            size=size, pagingMode='OFFSET',
            selection=SelectionDTO(expressions=[ExpressionDTO(terms=[TermDTO(
                property='contextId', value=context_id, operator='EQ')])])
        )
        count = 0
        total_count = -1

        while True:
            json_data = search_query_dto.dict(by_alias=True)
            response = self.requester.post(url='core/api/events/search', json=json_data)
            if response.status_code != 200:
                print(response)
                raise ProcessLookupError(response.content.decode())

            response_string = response.content.decode()
            event_list = EventDTOList.model_validate_json(response_string)
            yield from event_list.data
            if total_count == -1:
                total_count = event_list.totalCount
            count += len(event_list.data)
            if count >= total_count:
                break
            search_query_dto.from_ = count

    def get_delivery_from_context_string(self, context_string: str):
        search_query_dto = QueryDTO(
            size=10, pagingMode='OFFSET',
            selection=SelectionDTO(expressions=[ExpressionDTO(terms=[TermDTO(
                property='omschrijving', value=context_string, operator='CONTAINS')])])
        )

        json_data = search_query_dto.model_dump(by_alias=True)
        response = self.requester.post(url='core/api/eventcontexts/search', json=json_data)
        if response.status_code != 200:
            print(response)
            raise ProcessLookupError(response.content.decode())

        response_string = response.content.decode()
        return EventContextDTOList.model_validate_json(response_string)
