import json
from typing import Iterator, Generator

from API.AbstractRequester import AbstractRequester
from Domain.ZoekParameterOTL import ZoekParameterOTL


class EMsonImporter:
    def __init__(self, requester: AbstractRequester):
        self.requester = requester
        self.requester.first_part_url += 'emson/'

    def get_asset_by_uuid(self, uuid: str) -> dict:
        url = f'api/otl/assets/{uuid}'

        response = self.requester.get(url=url)
        decoded_string = response.content.decode()
        return json.loads(decoded_string)

    def get_assets_by_uuid_using_iterator(
            self,
            cursor: str | None = None,
            size: int = 100,
            uuids: [str] = None) -> Generator[dict, None, None]:

        url = 'api/otl/assets/search'

        while True:
            otl_zoekparameter = ZoekParameterOTL(size=size, from_cursor=cursor, filter_dict={'uuid': list(uuids)})
            json_data = otl_zoekparameter.to_dict_emson()

            response = self.requester.post(url=url, json=json_data)
            decoded_string = response.content.decode()

            if response.status_code != 200:
                raise RuntimeError(f"Error: {decoded_string}")

            graph = json.loads(decoded_string)
            headers = dict(response.headers)
            
            yield from graph['@graph']
            if 'em-paging-next-cursor' not in headers:
                break
            cursor = headers['em-paging-next-cursor']

    def get_assetrelaties_by_bron_doel_uuid_using_iterator(
            self,
            cursor: str | None = None,
            size: int = 100,
            uuids: [str] = None) -> Generator[dict, None, None]:

        url = 'api/otl/assetrelaties/search'

        while True:
            otl_zoekparameter = ZoekParameterOTL(size=size, from_cursor=cursor, filter_dict={'asset': list(uuids)})
            json_data = otl_zoekparameter.to_dict_emson()

            response = self.requester.post(url=url, json=json_data)
            decoded_string = response.content.decode()

            if response.status_code != 200:
                raise RuntimeError(f"Error: {decoded_string}")

            graph = json.loads(decoded_string)
            headers = dict(response.headers)

            yield from graph['@graph']
            if 'em-paging-next-cursor' not in headers:
                break
            cursor = headers['em-paging-next-cursor']

    def get_assetrelaties_by_uuid_using_iterator(
            self,
            cursor: str | None = None,
            size: int = 100,
            uuids: [str] = None) -> Generator[dict, None, None]:

        url = 'api/otl/assetrelaties/search'

        while True:
            otl_zoekparameter = ZoekParameterOTL(size=size, from_cursor=cursor, filter_dict={'uuid': list(uuids)})
            json_data = otl_zoekparameter.to_dict_emson()

            response = self.requester.post(url=url, json=json_data)
            decoded_string = response.content.decode()

            if response.status_code != 200:
                raise RuntimeError(f"Error: {decoded_string}")

            graph = json.loads(decoded_string)
            headers = dict(response.headers)

            yield from graph['@graph']
            if 'em-paging-next-cursor' not in headers:
                break
            cursor = headers['em-paging-next-cursor']

