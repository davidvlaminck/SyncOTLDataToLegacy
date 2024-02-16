﻿import logging
from unittest.mock import Mock

import pandas
from pandas import DataFrame

from AbstractRequester import AbstractRequester
from AssetInfoCollector import AssetInfoCollector
from EMInfraImporter import EMInfraImporter


def fake_get_objects_from_oslo_search_endpoint_using_iterator(resource: str, cursor: str | None = None,
                                                              size: int = 100, filter_dict: dict = None):
    asset_1 = {
        "@type": "https://lgc.data.wegenenverkeer.be/ns/installatie#Kast",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000001-bGdjOmluc3RhbGxhdGllI0thc3Q",
        "AIMDBStatus.isActief": True,
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000001-bGdjOmluc3RhbGxhdGllI0thc3Q"
        },
        "AIMObject.typeURI": "https://lgc.data.wegenenverkeer.be/ns/installatie#Kast",
        "tz:Schadebeheerder.schadebeheerder": {
            "tz:DtcBeheerder.naam": "District Schadebeheerder",
            "tz:DtcBeheerder.referentie": "100"
        },
        "AIMToestand.toestand": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlAIMToestand/in-gebruik",
        "AIMObject.notitie": "",
        "NaampadObject.naampad": "NAAMPAD/KAST",
        "AIMNaamObject.naam": "KAST",
        "loc:Locatie.omschrijving": "omschrijving",
    }
    asset_inactief = {
        "@type": "https://lgc.data.wegenenverkeer.be/ns/installatie#Kast",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000010-bGdjOmluc3RhbGxhdGllI0thc3Q",
        "AIMDBStatus.isActief": False
    }
    asset_2 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000002-",
        "AIMDBStatus.isActief": True,
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000002-"
        },
        "AIMObject.typeURI": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
    }
    asset_3 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000003-",
        "AIMDBStatus.isActief": True,
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000003-"
        },
        "AIMObject.typeURI": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
    }
    asset_4 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVLichtmast",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000004-",
        "AIMDBStatus.isActief": True,
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000004-"
        },
        "AIMObject.typeURI": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVLichtmast",
    }
    asset_5 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVConsole",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000005-",
        "AIMDBStatus.isActief": True,
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000005-"
        },
        "AIMObject.typeURI": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVConsole",
    }
    asset_6 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Armatuurcontroller",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000006-",
        "AIMDBStatus.isActief": True,
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000006-"
        },
        "AIMObject.typeURI": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Armatuurcontroller",
    }
    asset_7 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Armatuurcontroller",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000007-",
        "AIMDBStatus.isActief": True,
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000007-"
        },
        "AIMObject.typeURI": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Armatuurcontroller",
    }
    asset_8 = {
        "@type": "https://lgc.data.wegenenverkeer.be/ns/installatie#VPLMast",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000008-",
        "AIMDBStatus.isActief": True,
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000008-"
        },
        "AIMObject.typeURI": "https://lgc.data.wegenenverkeer.be/ns/installatie#VPLMast",
    }
    asset_9 = {
        "@type": "https://lgc.data.wegenenverkeer.be/ns/installatie#VPConsole",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000009-",
        "AIMDBStatus.isActief": True,
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000009-"
        },
        "AIMObject.typeURI": "https://lgc.data.wegenenverkeer.be/ns/installatie#VPConsole",
    }

    relatie_10 = {
        "@type": "https://grp.data.wegenenverkeer.be/ns/onderdeel#Bevestiging",
        "@id": "https://data.awvvlaanderen.be/id/assetrelatie/000000000002-Bevestigin-000000000004-",
        "RelatieObject.bron": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000002-"
        },
        "RelatieObject.doel": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVLichtmast",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000004-"
        }
    }
    relatie_11 = {
        "@type": "https://grp.data.wegenenverkeer.be/ns/onderdeel#Bevestiging",
        "@id": "https://data.awvvlaanderen.be/id/assetrelatie/000000000006-Bevestigin-000000000002-",
        "RelatieObject.bron": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Armatuurcontroller",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000006-"
        },
        "RelatieObject.doel": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000002-"
        }
    }
    relatie_12 = {
        "@type": "https://grp.data.wegenenverkeer.be/ns/onderdeel#Bevestiging",
        "@id": "https://data.awvvlaanderen.be/id/assetrelatie/000000000005-Bevestigin-000000000003-",
        "RelatieObject.bron": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVConsole",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000005-"
        },
        "RelatieObject.doel": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000003-"
        }
    }
    relatie_13 = {
        "@type": "https://grp.data.wegenenverkeer.be/ns/onderdeel#Bevestiging",
        "@id": "https://data.awvvlaanderen.be/id/assetrelatie/000000000003-Bevestigin-000000000007-",
        "RelatieObject.bron": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000003-"
        },
        "RelatieObject.doel": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Armatuurcontroller",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000007-"
        }
    }
    relatie_14 = {
        "@type": "https://grp.data.wegenenverkeer.be/ns/onderdeel#HoortBij",
        "@id": "https://data.awvvlaanderen.be/id/assetrelatie/000000000004--HoortBij--000000000008-",
        "RelatieObject.bron": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVLichtmast",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000004-"
        },
        "RelatieObject.doel": {
            "@type": "https://lgc.data.wegenenverkeer.be/ns/installatie#VPLMast",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000008-"
        }
    }
    relatie_15 = {
        "@type": "https://grp.data.wegenenverkeer.be/ns/onderdeel#HoortBij",
        "@id": "https://data.awvvlaanderen.be/id/assetrelatie/000000000005--HoortBij--000000000009-",
        "RelatieObject.bron": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVConsole",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000005-"
        },
        "RelatieObject.doel": {
            "@type": "https://lgc.data.wegenenverkeer.be/ns/installatie#VPConsole",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000009-"
        }
    }

    logging.debug(f'API Call made to get objects from oslo search endpoint using iterator, resource: {resource}')

    if resource == 'assets':
        yield from iter([a for a in [asset_1, asset_2, asset_3, asset_4, asset_5, asset_6, asset_7, asset_8, asset_9,
                                     asset_inactief]
                         if a['@id'][39:75] in filter_dict['uuid']])
    elif resource == 'assetrelaties':
        assetrelaties = [relatie_10, relatie_11, relatie_12, relatie_13, relatie_14, relatie_15]
        if 'uuid' in filter_dict:
            yield from iter([r for r in assetrelaties
                             if r['@id'][46:82] in filter_dict['uuid']])
        elif 'asset' in filter_dict:
            yield from iter([r for r in assetrelaties
                             if r['RelatieObject.bron']['@id'][39:75] in filter_dict['asset'] or
                             r['RelatieObject.doel']['@id'][39:75] in filter_dict['asset']])


fake_em_infra_importer = Mock(spec=EMInfraImporter)
fake_em_infra_importer.get_objects_from_oslo_search_endpoint_using_iterator = fake_get_objects_from_oslo_search_endpoint_using_iterator


def test_asset_info_collector():
    fake_requester = Mock(spec=AbstractRequester)
    fake_requester.first_part_url = ''
    AssetInfoCollector.create_requester_with_settings = Mock(return_value=fake_requester)
    collector = AssetInfoCollector(auth_type=Mock(), env=Mock(), settings_path=Mock())
    collector.em_infra_importer = fake_em_infra_importer

    collector.collect_asset_info(uuids=['00000000-0000-0000-0000-000000000001'])
    asset_node = collector.collection.get_node_object_by_uuid('00000000-0000-0000-0000-000000000001')
    assert asset_node.uuid == '00000000-0000-0000-0000-000000000001'


def test_asset_info_collector_inactive():
    fake_requester = Mock(spec=AbstractRequester)
    fake_requester.first_part_url = ''
    AssetInfoCollector.create_requester_with_settings = Mock(return_value=fake_requester)
    collector = AssetInfoCollector(auth_type=Mock(), env=Mock(), settings_path=Mock())
    collector.em_infra_importer = fake_em_infra_importer

    collector.collect_asset_info(uuids=['00000000-0000-0000-0000-000000000010'])
    asset_node = collector.collection.get_node_object_by_uuid('00000000-0000-0000-0000-000000000010')
    assert asset_node.uuid == '00000000-0000-0000-0000-000000000010'
    assert asset_node.active is False


def test_start_collecting_from_starting_uuids():
    fake_requester = Mock(spec=AbstractRequester)
    fake_requester.first_part_url = ''
    AssetInfoCollector.create_requester_with_settings = Mock(return_value=fake_requester)
    collector = AssetInfoCollector(auth_type=Mock(), env=Mock(), settings_path=Mock())
    collector.em_infra_importer = fake_em_infra_importer

    collector.start_collecting_from_starting_uuids(
        starting_uuids=['00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000003'])

    assert collector.collection.short_uri_dict == {
        'onderdeel#VerlichtingstoestelLED': {'00000000-0000-0000-0000-000000000002',
                                             '00000000-0000-0000-0000-000000000003'},
        'onderdeel#WVLichtmast': {'00000000-0000-0000-0000-000000000004'},
        'onderdeel#WVConsole': {'00000000-0000-0000-0000-000000000005'},
        'onderdeel#Armatuurcontroller': {'00000000-0000-0000-0000-000000000006',
                                         '00000000-0000-0000-0000-000000000007'},
        'lgc:installatie#VPLMast': {'00000000-0000-0000-0000-000000000008'},
        'lgc:installatie#VPConsole': {'00000000-0000-0000-0000-000000000009'},
        'onderdeel#Bevestiging': {'000000000002-Bevestigin-000000000004',
                                  '000000000006-Bevestigin-000000000002',
                                  '000000000005-Bevestigin-000000000003',
                                  '000000000003-Bevestigin-000000000007'},
        'onderdeel#HoortBij': {'000000000004--HoortBij--000000000008',
                               '000000000005--HoortBij--000000000009'}
    }


def test_start_creating_report():
    fake_requester = Mock(spec=AbstractRequester)
    fake_requester.first_part_url = ''
    AssetInfoCollector.create_requester_with_settings = Mock(return_value=fake_requester)
    collector = AssetInfoCollector(auth_type=Mock(), env=Mock(), settings_path=Mock())
    collector.em_infra_importer = fake_em_infra_importer

    collector.collect_asset_info(
        uuids=['00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000003',
               '00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000005',
               '00000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000007',
               '00000000-0000-0000-0000-000000000008', '00000000-0000-0000-0000-000000000009'])
    collector.collect_relation_info(
        uuids=['000000000002-Bevestigin-000000000004', '000000000006-Bevestigin-000000000002',
               '000000000005-Bevestigin-000000000003', '000000000003-Bevestigin-000000000007',
               '000000000004--HoortBij--000000000008', '000000000005--HoortBij--000000000009'])

    expected_report = {
        'columns': [
            'aanlevering_id', 'aanlevering_naam', 'LED_toestel_uuid', 'LED_toestel_naam',
            'relatie_naar_armatuur_controller_aanwezig', 'armatuur_controller_uuid', 'armatuur_controller_naam',
            'relatie_naar_drager_aanwezig', 'drager_uuid', 'drager_type', 'drager_naam',
            'relatie_naar_legacy_drager_aanwezig', 'legacy_drager_uuid', 'legacy_drager_type', 'legacy_drager_naampad'],
        'index': [0, 0],
        'data': [
            ['01', 'DA-01', '00000000-0000-0000-0000-000000000002', '',
             True, '00000000-0000-0000-0000-000000000006', '',
             True, '00000000-0000-0000-0000-000000000004', 'WVLichtmast', '',
             True, '00000000-0000-0000-0000-000000000008', 'VPLMast', ''],
            ['01', 'DA-01', '00000000-0000-0000-0000-000000000003', '',
             True, '00000000-0000-0000-0000-000000000007', '',
             True, '00000000-0000-0000-0000-000000000005', 'WVConsole', '',
             True, '00000000-0000-0000-0000-000000000009', 'VPConsole', '']]}

    report = collector.start_creating_report('01', 'DA-01')

    assert report.to_dict('split') == expected_report
