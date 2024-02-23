import os
import sqlite3
from pathlib import Path
from unittest.mock import Mock

from API.AbstractRequester import AbstractRequester
from API.EMInfraRestClient import EMInfraRestClient
from Database.DbManager import DbManager
from Domain.DeliveryFinder import DeliveryFinder
from Domain.EMInfraDomain import FeedProxyPage, ProxyEntryObject, Link


def fake_get_current_feed_page() -> FeedProxyPage:
    return FeedProxyPage(
        id='Proxied EM-Infra change feed for assets',
        entries=[ProxyEntryObject(id='2', _type='atom', updated='2021-10-01T13:00:00Z'),
                 ProxyEntryObject(id='1', _type='atom', updated='2021-10-01T12:00:00Z')],
        links=[Link(rel='self', href='/10/100'), Link(rel='last', href='/0/100')])


fake_em_infra_importer = Mock(spec=EMInfraRestClient)
fake_em_infra_importer.get_current_feed_page = fake_get_current_feed_page


def test_get_page_number_and_event_from_api():
    fake_requester = Mock(spec=AbstractRequester)
    fake_requester.first_part_url = ''
    DeliveryFinder.create_requester_with_settings = Mock(return_value=fake_requester)
    delivery_finder = DeliveryFinder(em_infra_client=fake_em_infra_importer, davie_client=Mock(), db_manager=Mock())
    feedproxy_page_number, last_event_id = delivery_finder.get_page_number_and_event_from_api()
    assert feedproxy_page_number == '10'
    assert last_event_id == '2'


def test_get_page_number_and_event_from_api():
    page = fake_get_current_feed_page()
    assert DeliveryFinder.is_last_event_in_feedproxy(page, '2')
    assert not DeliveryFinder.is_last_event_in_feedproxy(page, '1')
