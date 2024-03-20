﻿import logging
from copy import deepcopy
from unittest.mock import Mock

import pytest

from API.AbstractRequester import AbstractRequester
from API.EMInfraRestClient import EMInfraRestClient
from Domain.AssetInfoCollector import AssetInfoCollector
from Domain.InfoObject import NodeInfoObject


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
        'AIMNaamObject.naam': 'A0000.A01.WV1',
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000002-"
        },
        "AIMObject.datumOprichtingObject": "2020-01-01",
        "AIMObject.typeURI": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
        "VerlichtingstoestelLED.kleurTemperatuur": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedKleurTemp/3000",
        "Verlichtingstoestel.systeemvermogen": 100,
        "Verlichtingstoestel.modelnaam": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlVerlichtingstoestelModelnaam/ampera",
        "Verlichtingstoestel.merk": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlVerlichtingstoestelMerk/Schreder",
        "VerlichtingstoestelLED.lichtpuntHoogte": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedLichtpunthoogte/6",
        "VerlichtingstoestelLED.aantalTeVerlichtenRijstroken": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedAantalTeVerlichtenRijstroken/1",
        "VerlichtingstoestelLED.lumenOutput": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlLumenOutput/10000",
        "VerlichtingstoestelLED.overhang": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedOverhang/1-0",
        "Verlichtingstoestel.verlichtGebied": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlVerlichtingstoestelVerlichtGebied/hoofdweg",
        "VerlichtingstoestelLED.verlichtingsNiveau": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedVerlNiveau/M3",
    }
    asset_3 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000003-",
        "AIMDBStatus.isActief": True,
        'AIMNaamObject.naam': 'A0000.C02.WV1',
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
        'AIMNaamObject.naam': 'A0000.A01',
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000004-"
        },
        "AIMObject.typeURI": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVLichtmast",
        "geo:Geometrie.log": [
            {
                "geo:DtcLog.bron": "https://geo.data.wegenenverkeer.be/id/concept/KlLogBron/meettoestel",
                "geo:DtcLog.niveau": "https://geo.data.wegenenverkeer.be/id/concept/KlLogNiveau/0",
                "geo:DtcLog.geometrie": {
                    "geo:DtuGeometrie.punt": "POINT Z (200000.00 200001.00 0)"
                },
            }
        ],
        "AIMToestand.toestand": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlAIMToestand/in-gebruik",
        "Lichtmast.kleur": "7038"
    }
    asset_5 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVConsole",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000005-",
        "AIMDBStatus.isActief": True,
        'AIMNaamObject.naam': 'A0000.FOUT1',
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000005-"
        },
        "AIMObject.typeURI": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVConsole",
        "AIMToestand.toestand": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlAIMToestand/uit-gebruik",
    }
    asset_6 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Armatuurcontroller",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000006-",
        "AIMDBStatus.isActief": True,
        'AIMNaamObject.naam': 'A0000.A01.WV1.AC1',
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000006-"
        },
        "AIMObject.typeURI": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Armatuurcontroller",
        "Armatuurcontroller.serienummer": '1234561'
    }
    asset_7 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Armatuurcontroller",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000007-",
        "AIMDBStatus.isActief": True,
        'AIMNaamObject.naam': 'A0000.C02.WV1.AC1',
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
        'AIMNaamObject.naam': 'A01',
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000008-"
        },
        "AIMObject.typeURI": "https://lgc.data.wegenenverkeer.be/ns/installatie#VPLMast",
        "NaampadObject.naampad": "A0000/A0000.WV/A01",
        "loc:Locatie.puntlocatie": {
            "loc:DtcPuntlocatie.bron": "https://loc.data.wegenenverkeer.be/id/concept/KlLocatieBron/manueel",
            "loc:3Dpunt.puntgeometrie": {
                "loc:DtcCoord.lambert72": {
                    "loc:DtcCoordLambert72.ycoordinaat": 200001.0,
                    "loc:DtcCoordLambert72.zcoordinaat": 0,
                    "loc:DtcCoordLambert72.xcoordinaat": 200001.0
                }
            },
            "loc:DtcPuntlocatie.precisie": "https://loc.data.wegenenverkeer.be/id/concept/KlLocatiePrecisie/meter"
        },
        "AIMToestand.toestand": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlAIMToestand/in-gebruik",
        'lgc:EMObject.aantalTeVerlichtenRijvakkenLed': 'R1',
        'lgc:EMObject.aantalVerlichtingstoestellen': 4,
        'lgc:EMObject.contractnummerLeveringLed': '123456',
        'lgc:EMObject.datumInstallatieLed': '2020-01-01',
        'lgc:EMObject.kleurtemperatuurLed': 'K3000',
        'lgc:EMObject.ledVerlichting': True,
        'lgc:VPLMast.lichtmastBuitenGebruik': False,
        'lgc:EMObject.lichtpunthoogteTovRijweg': 6,
        'lgc:EMObject.lumenPakketLed': 10000,
        'lgc:EMObject.overhangLed': 'O+1',
        'lgc:VPLMast.ralKleurVplmast': '7038',
        'lgc:VPLMast.serienummerArmatuurcontroller1': '1234561',
        'lgc:VPLMast.serienummerArmatuurcontroller2': '1234562',
        'lgc:VPLMast.serienummerArmatuurcontroller3': '1234563',
        'lgc:VPLMast.serienummerArmatuurcontroller4': '1234564',
        'lgc:EMObject.verlichtingsniveauLed': 'M3',
        'lgc:EMObject.verlichtingstoestelMerkEnType': 'Schreder Ampera',
        'lgc:EMObject.verlichtingstoestelSysteemvermogen': 100,
        'lgc:EMObject.verlichtingstype': 'hoofdbaan'
    }
    asset_9 = {
        "@type": "https://lgc.data.wegenenverkeer.be/ns/installatie#VPConsole",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000009-",
        "AIMDBStatus.isActief": True,
        'AIMNaamObject.naam': 'C02',
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000009-"
        },
        "AIMObject.typeURI": "https://lgc.data.wegenenverkeer.be/ns/installatie#VPConsole",
        "NaampadObject.naampad": "A0000/A0000.WV/C02",
        "AIMToestand.toestand": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlAIMToestand/in-gebruik",
        'lgc:EMObject.aantalTeVerlichtenRijvakkenLed': 'R2',
        'lgc:EMObject.aantalVerlichtingstoestellen': 1,
        'lgc:EMObject.contractnummerLeveringLed': '123456',
        'lgc:EMObject.datumInstallatieLed': '2020-01-01',
        'lgc:EMObject.kleurtemperatuurLed': 'K3000',
        'lgc:EMObject.ledVerlichting': True,
        'lgc:VPConsole.consoleBuitenGebruik': False,
        'lgc:EMObject.lichtpunthoogteTovRijweg': 5,
        'lgc:EMObject.lumenPakketLed': 10000,
        'lgc:EMObject.overhangLed': '0',
        'lgc:VPConsole.ralKleurVpconsole': '7038',
        'lgc:EMObject.serienummerArmatuurcontroller': '1234561',
        'lgc:EMObject.verlichtingsniveauLed': 'M2',
        'lgc:EMObject.verlichtingstoestelMerkEnType': 'Schreder Ampera',
        'lgc:EMObject.verlichtingstoestelSysteemvermogen': 100,
        'lgc:EMObject.verlichtingstype': 'hoofdbaan'
    }

    relatie_10 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Bevestiging",
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
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Bevestiging",
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
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Bevestiging",
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
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Bevestiging",
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

    asset_21 = {
        "@type": "https://lgc.data.wegenenverkeer.be/ns/installatie#VPBevestig",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000021-",
        "AIMDBStatus.isActief": True,
        'AIMNaamObject.naam': 'C03',
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000021-"
        },
        "AIMObject.typeURI": "https://lgc.data.wegenenverkeer.be/ns/installatie#VPBevestig",
        "NaampadObject.naampad": "A0000/A0000.WV/C03",
        "AIMToestand.toestand": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlAIMToestand/in-gebruik",
    }

    asset_22 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000022-",
        "AIMDBStatus.isActief": True,
        'AIMNaamObject.naam': 'A0000.A01.WV2',
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000022-"
        },
        "AIMObject.datumOprichtingObject": "2020-01-01",
        "AIMObject.typeURI": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
        "VerlichtingstoestelLED.kleurTemperatuur": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedKleurTemp/3000",
        "Verlichtingstoestel.systeemvermogen": 100,
        "Verlichtingstoestel.modelnaam": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlVerlichtingstoestelModelnaam/ampera",
        "Verlichtingstoestel.merk": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlVerlichtingstoestelMerk/Schreder",
        "VerlichtingstoestelLED.lichtpuntHoogte": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedLichtpunthoogte/6",
        "VerlichtingstoestelLED.aantalTeVerlichtenRijstroken": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedAantalTeVerlichtenRijstroken/1",
        "VerlichtingstoestelLED.lumenOutput": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlLumenOutput/10000",
        "VerlichtingstoestelLED.overhang": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedOverhang/1-0",
        "Verlichtingstoestel.verlichtGebied": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlVerlichtingstoestelVerlichtGebied/hoofdweg",
        "VerlichtingstoestelLED.verlichtingsNiveau": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedVerlNiveau/M3",
    }
    asset_23 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000023-",
        "AIMDBStatus.isActief": True,
        'AIMNaamObject.naam': 'A0000.A01.WV3',
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000023-"
        },
        "AIMObject.datumOprichtingObject": "2020-01-01",
        "AIMObject.typeURI": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
        "VerlichtingstoestelLED.kleurTemperatuur": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedKleurTemp/3000",
        "Verlichtingstoestel.systeemvermogen": 100,
        "Verlichtingstoestel.modelnaam": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlVerlichtingstoestelModelnaam/ampera",
        "Verlichtingstoestel.merk": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlVerlichtingstoestelMerk/Schreder",
        "VerlichtingstoestelLED.lichtpuntHoogte": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedLichtpunthoogte/6",
        "VerlichtingstoestelLED.aantalTeVerlichtenRijstroken": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedAantalTeVerlichtenRijstroken/1",
        "VerlichtingstoestelLED.lumenOutput": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlLumenOutput/10000",
        "VerlichtingstoestelLED.overhang": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedOverhang/1",
        "Verlichtingstoestel.verlichtGebied": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlVerlichtingstoestelVerlichtGebied/hoofdweg",
        "VerlichtingstoestelLED.verlichtingsNiveau": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedVerlNiveau/M3",
    }
    asset_24 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000024-",
        "AIMDBStatus.isActief": True,
        'AIMNaamObject.naam': 'A0000.A01.WV4',
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000024-"
        },
        "AIMObject.datumOprichtingObject": "2020-01-01",
        "AIMObject.typeURI": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
        "VerlichtingstoestelLED.kleurTemperatuur": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedKleurTemp/3000",
        "Verlichtingstoestel.systeemvermogen": 100,
        "Verlichtingstoestel.modelnaam": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlVerlichtingstoestelModelnaam/ampera",
        "Verlichtingstoestel.merk": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlVerlichtingstoestelMerk/Schreder",
        "VerlichtingstoestelLED.lichtpuntHoogte": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedLichtpunthoogte/6",
        "VerlichtingstoestelLED.aantalTeVerlichtenRijstroken": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedAantalTeVerlichtenRijstroken/1",
        "VerlichtingstoestelLED.lumenOutput": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlLumenOutput/10000",
        "VerlichtingstoestelLED.overhang": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedOverhang/1",
        "Verlichtingstoestel.verlichtGebied": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlVerlichtingstoestelVerlichtGebied/hoofdweg",
        "VerlichtingstoestelLED.verlichtingsNiveau": "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedVerlNiveau/M3",
    }
    asset_25 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000025-",
        "AIMDBStatus.isActief": True,
        'AIMNaamObject.naam': 'A0000.C03.WV1',
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000025-"
        },
        "AIMObject.datumOprichtingObject": "2020-01-01",
        "AIMObject.typeURI": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
    }
    asset_26 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Armatuurcontroller",
        "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000026-",
        "AIMDBStatus.isActief": True,
        'AIMNaamObject.naam': 'A0000.A01.WV2.AC1',
        "AIMObject.assetId": {
            "DtcIdentificator.toegekendDoor": "AWV",
            "DtcIdentificator.identificator": "00000000-0000-0000-0000-000000000026-"
        },
        "AIMObject.typeURI": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Armatuurcontroller",
        "Armatuurcontroller.serienummer": '1234562'
    }

    relatie_31 = {
        "@type": "https://grp.data.wegenenverkeer.be/ns/onderdeel#HoortBij",
        "@id": "https://data.awvvlaanderen.be/id/assetrelatie/000000000025--HoortBij--000000000021-",
        "RelatieObject.bron": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000025-"
        },
        "RelatieObject.doel": {
            "@type": "https://lgc.data.wegenenverkeer.be/ns/installatie#VPBevestig",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000021-"
        }
    }
    relatie_32 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Bevestiging",
        "@id": "https://data.awvvlaanderen.be/id/assetrelatie/000000000022-Bevestigin-000000000004-",
        "RelatieObject.bron": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000022-"
        },
        "RelatieObject.doel": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVLichtmast",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000004-"
        }
    }
    relatie_33 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Bevestiging",
        "@id": "https://data.awvvlaanderen.be/id/assetrelatie/000000000023-Bevestigin-000000000004-",
        "RelatieObject.bron": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000023-"
        },
        "RelatieObject.doel": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVLichtmast",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000004-"
        }
    }
    relatie_34 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Bevestiging",
        "@id": "https://data.awvvlaanderen.be/id/assetrelatie/000000000024-Bevestigin-000000000004-",
        "RelatieObject.bron": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000024-"
        },
        "RelatieObject.doel": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVLichtmast",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000004-"
        }
    }
    relatie_35 = {
        "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Bevestiging",
        "@id": "https://data.awvvlaanderen.be/id/assetrelatie/000000000002-Bevestigin-000000000026-",
        "RelatieObject.bron": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VerlichtingstoestelLED",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000002-"
        },
        "RelatieObject.doel": {
            "@type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Armatuurcontroller",
            "@id": "https://data.awvvlaanderen.be/id/asset/00000000-0000-0000-0000-000000000026-"
        }
    }

    logging.debug(f'API Call made to get objects from oslo search endpoint using iterator, resource: {resource}')

    if resource == 'assets':
        yield from iter([a for a in [asset_1, asset_2, asset_3, asset_4, asset_5, asset_6, asset_7, asset_8, asset_9,
                                     asset_inactief, asset_21, asset_22, asset_23, asset_24, asset_25, asset_26]
                         if a['@id'][39:75] in filter_dict['uuid']])
    elif resource == 'assetrelaties':
        assetrelaties = [relatie_10, relatie_11, relatie_12, relatie_13, relatie_14, relatie_15,
                         relatie_31, relatie_32, relatie_33, relatie_34, relatie_35]
        if 'uuid' in filter_dict:
            yield from iter([r for r in assetrelaties
                             if r['@id'][46:82] in filter_dict['uuid']])
        elif 'asset' in filter_dict:
            yield from iter([r for r in assetrelaties
                             if r['RelatieObject.bron']['@id'][39:75] in filter_dict['asset'] or
                             r['RelatieObject.doel']['@id'][39:75] in filter_dict['asset']])


fake_em_infra_importer = Mock(spec=EMInfraRestClient)
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


def test_start_collecting_from_starting_uuids_using_pattern_giving_uuids_of_a():
    fake_requester = Mock(spec=AbstractRequester)
    fake_requester.first_part_url = ''
    AssetInfoCollector.create_requester_with_settings = Mock(return_value=fake_requester)
    collector = AssetInfoCollector(auth_type=Mock(), env=Mock(), settings_path=Mock())
    collector.em_infra_importer = fake_em_infra_importer

    collector.start_collecting_from_starting_uuids_using_pattern(
        starting_uuids=['00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000003',
                        '00000000-0000-0000-0000-000000000025'],
        pattern=[('uuids', 'of', 'a'),
                 ('a', 'type_of', ['onderdeel#VerlichtingstoestelLED']),
                 ('a', '-[r1]-', 'b'),
                 ('b', 'type_of', ['onderdeel#WVLichtmast', 'onderdeel#WVConsole', 'onderdeel#Armatuurcontroller']),
                 ('b', '-[r2]->', 'c'),
                 ('a', '-[r2]->', 'c'),
                 ('c', 'type_of', ['lgc:installatie#VPLMast', 'lgc:installatie#VPConsole',
                                   'lgc:installatie#VPBevestig']),
                 ('r1', 'type_of', ['onderdeel#Bevestiging']),
                 ('r2', 'type_of', ['onderdeel#HoortBij'])])

    assert collector.collection.short_uri_dict == {'lgc:installatie#VPBevestig': {'00000000-0000-0000-0000-000000000021'},
 'lgc:installatie#VPConsole': {'00000000-0000-0000-0000-000000000009'},
 'lgc:installatie#VPLMast': {'00000000-0000-0000-0000-000000000008'},
 'onderdeel#Armatuurcontroller': {'00000000-0000-0000-0000-000000000006',
                                  '00000000-0000-0000-0000-000000000007',
                                  '00000000-0000-0000-0000-000000000026'},
 'onderdeel#Bevestiging': {'000000000002-Bevestigin-000000000004',
                           '000000000002-Bevestigin-000000000026',
                           '000000000003-Bevestigin-000000000007',
                           '000000000005-Bevestigin-000000000003',
                           '000000000006-Bevestigin-000000000002',
                           '000000000022-Bevestigin-000000000004',
                           '000000000023-Bevestigin-000000000004',
                           '000000000024-Bevestigin-000000000004'},
 'onderdeel#HoortBij': {'000000000004--HoortBij--000000000008',
                        '000000000005--HoortBij--000000000009',
                        '000000000025--HoortBij--000000000021'},
 'onderdeel#VerlichtingstoestelLED': {'00000000-0000-0000-0000-000000000002',
                                      '00000000-0000-0000-0000-000000000003',
                                      '00000000-0000-0000-0000-000000000022',
                                      '00000000-0000-0000-0000-000000000023',
                                      '00000000-0000-0000-0000-000000000024',
                                      '00000000-0000-0000-0000-000000000025'},
 'onderdeel#WVConsole': {'00000000-0000-0000-0000-000000000005'},
 'onderdeel#WVLichtmast': {'00000000-0000-0000-0000-000000000004'}}


def test_start_collecting_from_starting_uuids_using_pattern_giving_uuids_of_c():
    fake_requester = Mock(spec=AbstractRequester)
    fake_requester.first_part_url = ''
    AssetInfoCollector.create_requester_with_settings = Mock(return_value=fake_requester)
    collector = AssetInfoCollector(auth_type=Mock(), env=Mock(), settings_path=Mock())
    collector.em_infra_importer = fake_em_infra_importer

    collector.start_collecting_from_starting_uuids_using_pattern(
        starting_uuids=['00000000-0000-0000-0000-000000000008', '00000000-0000-0000-0000-000000000009'],
        pattern=[('uuids', 'of', 'c'),
                 ('a', 'type_of', ['onderdeel#VerlichtingstoestelLED']),
                 ('a', '-[r1]-', 'b'),
                 ('b', 'type_of', ['onderdeel#WVLichtmast', 'onderdeel#WVConsole']),
                 ('a', '-[r1]-', 'd'),
                 ('d', 'type_of', ['onderdeel#Armatuurcontroller']),
                 ('b', '-[r2]->', 'c'),
                 ('c', 'type_of', ['lgc:installatie#VPLMast', 'lgc:installatie#VPConsole']),
                 ('r1', 'type_of', ['onderdeel#Bevestiging']),
                 ('r2', 'type_of', ['onderdeel#HoortBij'])])

    assert collector.collection.short_uri_dict == {
        'lgc:installatie#VPConsole': {'00000000-0000-0000-0000-000000000009'},
        'lgc:installatie#VPLMast': {'00000000-0000-0000-0000-000000000008'},
        'onderdeel#Armatuurcontroller': {'00000000-0000-0000-0000-000000000006',
                                         '00000000-0000-0000-0000-000000000007',
                                         '00000000-0000-0000-0000-000000000026'},
        'onderdeel#Bevestiging': {'000000000002-Bevestigin-000000000004',
                                  '000000000002-Bevestigin-000000000026',
                                  '000000000003-Bevestigin-000000000007',
                                  '000000000005-Bevestigin-000000000003',
                                  '000000000006-Bevestigin-000000000002',
                                  '000000000022-Bevestigin-000000000004',
                                  '000000000023-Bevestigin-000000000004',
                                  '000000000024-Bevestigin-000000000004'},
        'onderdeel#HoortBij': {'000000000004--HoortBij--000000000008',
                               '000000000005--HoortBij--000000000009'},
        'onderdeel#VerlichtingstoestelLED': {'00000000-0000-0000-0000-000000000002',
                                             '00000000-0000-0000-0000-000000000003',
                                             '00000000-0000-0000-0000-000000000022',
                                             '00000000-0000-0000-0000-000000000023',
                                             '00000000-0000-0000-0000-000000000024'},
        'onderdeel#WVConsole': {'00000000-0000-0000-0000-000000000005'},
        'onderdeel#WVLichtmast': {'00000000-0000-0000-0000-000000000004'}}


def test_start_collecting_from_starting_uuids_using_pattern_giving_uuids_of_d():
    fake_requester = Mock(spec=AbstractRequester)
    fake_requester.first_part_url = ''
    AssetInfoCollector.create_requester_with_settings = Mock(return_value=fake_requester)
    collector = AssetInfoCollector(auth_type=Mock(), env=Mock(), settings_path=Mock())
    collector.em_infra_importer = fake_em_infra_importer

    collector.start_collecting_from_starting_uuids_using_pattern(
        starting_uuids=['00000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000007'],
        pattern=[('uuids', 'of', 'd'),
                 ('a', 'type_of', ['onderdeel#VerlichtingstoestelLED']),
                 ('a', '-[r1]-', 'b'),
                 ('b', 'type_of', ['onderdeel#WVLichtmast', 'onderdeel#WVConsole']),
                 ('a', '-[r1]-', 'd'),
                 ('d', 'type_of', ['onderdeel#Armatuurcontroller']),
                 ('b', '-[r2]->', 'c'),
                 ('c', 'type_of', ['lgc:installatie#VPLMast', 'lgc:installatie#VPConsole']),
                 ('r1', 'type_of', ['onderdeel#Bevestiging']),
                 ('r2', 'type_of', ['onderdeel#HoortBij'])])

    assert collector.collection.short_uri_dict == {
        'lgc:installatie#VPConsole': {'00000000-0000-0000-0000-000000000009'},
        'lgc:installatie#VPLMast': {'00000000-0000-0000-0000-000000000008'},
        'onderdeel#Armatuurcontroller': {'00000000-0000-0000-0000-000000000006',
                                         '00000000-0000-0000-0000-000000000007',
                                         '00000000-0000-0000-0000-000000000026'},
        'onderdeel#Bevestiging': {'000000000002-Bevestigin-000000000004',
                                  '000000000002-Bevestigin-000000000026',
                                  '000000000003-Bevestigin-000000000007',
                                  '000000000005-Bevestigin-000000000003',
                                  '000000000006-Bevestigin-000000000002',
                                  '000000000022-Bevestigin-000000000004',
                                  '000000000023-Bevestigin-000000000004',
                                  '000000000024-Bevestigin-000000000004'},
        'onderdeel#HoortBij': {'000000000004--HoortBij--000000000008',
                               '000000000005--HoortBij--000000000009'},
        'onderdeel#VerlichtingstoestelLED': {'00000000-0000-0000-0000-000000000002',
                                             '00000000-0000-0000-0000-000000000003',
                                             '00000000-0000-0000-0000-000000000022',
                                             '00000000-0000-0000-0000-000000000023',
                                             '00000000-0000-0000-0000-000000000024'},
        'onderdeel#WVConsole': {'00000000-0000-0000-0000-000000000005'},
        'onderdeel#WVLichtmast': {'00000000-0000-0000-0000-000000000004'}}


def test_start_collecting_from_starting_uuids_using_pattern_giving_uuids_of_b():
    fake_requester = Mock(spec=AbstractRequester)
    fake_requester.first_part_url = ''
    AssetInfoCollector.create_requester_with_settings = Mock(return_value=fake_requester)
    collector = AssetInfoCollector(auth_type=Mock(), env=Mock(), settings_path=Mock())
    collector.em_infra_importer = fake_em_infra_importer

    collector.start_collecting_from_starting_uuids_using_pattern(
        starting_uuids=['00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000005'],
        pattern=[('uuids', 'of', 'b'),
                 ('a', 'type_of', ['onderdeel#VerlichtingstoestelLED']),
                 ('a', '-[r1]-', 'b'),
                 ('b', 'type_of', ['onderdeel#WVLichtmast', 'onderdeel#WVConsole']),
                 ('a', '-[r1]-', 'd'),
                 ('d', 'type_of', ['onderdeel#Armatuurcontroller']),
                 ('b', '-[r2]->', 'c'),
                 ('c', 'type_of', ['lgc:installatie#VPLMast', 'lgc:installatie#VPConsole']),
                 ('r1', 'type_of', ['onderdeel#Bevestiging']),
                 ('r2', 'type_of', ['onderdeel#HoortBij'])])

    assert collector.collection.short_uri_dict == {
        'lgc:installatie#VPConsole': {'00000000-0000-0000-0000-000000000009'},
        'lgc:installatie#VPLMast': {'00000000-0000-0000-0000-000000000008'},
        'onderdeel#Armatuurcontroller': {'00000000-0000-0000-0000-000000000006',
                                         '00000000-0000-0000-0000-000000000007',
                                         '00000000-0000-0000-0000-000000000026'},
        'onderdeel#Bevestiging': {'000000000002-Bevestigin-000000000004',
                                  '000000000002-Bevestigin-000000000026',
                                  '000000000003-Bevestigin-000000000007',
                                  '000000000005-Bevestigin-000000000003',
                                  '000000000006-Bevestigin-000000000002',
                                  '000000000022-Bevestigin-000000000004',
                                  '000000000023-Bevestigin-000000000004',
                                  '000000000024-Bevestigin-000000000004'},
        'onderdeel#HoortBij': {'000000000004--HoortBij--000000000008',
                               '000000000005--HoortBij--000000000009'},
        'onderdeel#VerlichtingstoestelLED': {'00000000-0000-0000-0000-000000000002',
                                             '00000000-0000-0000-0000-000000000003',
                                             '00000000-0000-0000-0000-000000000022',
                                             '00000000-0000-0000-0000-000000000023',
                                             '00000000-0000-0000-0000-000000000024'},
        'onderdeel#WVConsole': {'00000000-0000-0000-0000-000000000005'},
        'onderdeel#WVLichtmast': {'00000000-0000-0000-0000-000000000004'}}


def test_start_collecting_from_starting_uuids():
    fake_requester = Mock(spec=AbstractRequester)
    fake_requester.first_part_url = ''
    AssetInfoCollector.create_requester_with_settings = Mock(return_value=fake_requester)
    collector = AssetInfoCollector(auth_type=Mock(), env=Mock(), settings_path=Mock())
    collector.em_infra_importer = fake_em_infra_importer

    collector.start_collecting_from_starting_uuids(
        starting_uuids=['00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000003'])

    assert collector.collection.short_uri_dict == {
        'lgc:installatie#VPConsole': {'00000000-0000-0000-0000-000000000009'},
        'lgc:installatie#VPLMast': {'00000000-0000-0000-0000-000000000008'},
        'onderdeel#Armatuurcontroller': {'00000000-0000-0000-0000-000000000006',
                                         '00000000-0000-0000-0000-000000000007',
                                         '00000000-0000-0000-0000-000000000026'},
        'onderdeel#Bevestiging': {'000000000002-Bevestigin-000000000004',
                                  '000000000002-Bevestigin-000000000026',
                                  '000000000003-Bevestigin-000000000007',
                                  '000000000005-Bevestigin-000000000003',
                                  '000000000006-Bevestigin-000000000002',
                                  '000000000022-Bevestigin-000000000004',
                                  '000000000023-Bevestigin-000000000004',
                                  '000000000024-Bevestigin-000000000004'},
        'onderdeel#HoortBij': {'000000000004--HoortBij--000000000008',
                               '000000000005--HoortBij--000000000009'},
        'onderdeel#VerlichtingstoestelLED': {'00000000-0000-0000-0000-000000000002',
                                             '00000000-0000-0000-0000-000000000003',
                                             '00000000-0000-0000-0000-000000000022',
                                             '00000000-0000-0000-0000-000000000023',
                                             '00000000-0000-0000-0000-000000000024'},
        'onderdeel#WVConsole': {'00000000-0000-0000-0000-000000000005'},
        'onderdeel#WVLichtmast': {'00000000-0000-0000-0000-000000000004'}}


def test_reverse_relation_pattern():
    reversed1 = AssetInfoCollector.reverse_relation_pattern(('a', '-[r1]-', 'b'))
    assert reversed1 == ('b', '-[r1]-', 'a')

    reversed2 = AssetInfoCollector.reverse_relation_pattern(('a', '-[r1]->', 'b'))
    assert reversed2 == ('b', '<-[r1]-', 'a')

    reversed3 = AssetInfoCollector.reverse_relation_pattern(('a', '<-[r1]->', 'b'))
    assert reversed3 == ('b', '<-[r1]->', 'a')

    reversed4 = AssetInfoCollector.reverse_relation_pattern(('a', '<-[r1]-', 'b'))
    assert reversed4 == ('b', '-[r1]->', 'a')


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
               '00000000-0000-0000-0000-000000000008', '00000000-0000-0000-0000-000000000009',
               '00000000-0000-0000-0000-000000000026', '00000000-0000-0000-0000-000000000022',
               '00000000-0000-0000-0000-000000000023', '00000000-0000-0000-0000-000000000024'])
    collector.collect_relation_info(
        uuids=['000000000002-Bevestigin-000000000004', '000000000006-Bevestigin-000000000002',
               '000000000005-Bevestigin-000000000003', '000000000003-Bevestigin-000000000007',
               '000000000004--HoortBij--000000000008', '000000000005--HoortBij--000000000009',
               '000000000024-Bevestigin-000000000004', '000000000023-Bevestigin-000000000004',
               '000000000022-Bevestigin-000000000004', '000000000002-Bevestigin-000000000026'])

    expected_report = {
        'columns': [
            'aanlevering_id', 'aanlevering_naam', 'legacy_drager_uuid', 'legacy_drager_type',
            'legacy_drager_naampad', 'legacy_drager_naampad_conform_conventie',
            'drager_verwacht', 'relatie_legacy_naar_drager_aanwezig',
            'drager_uuid', 'drager_type', 'drager_naam', 'drager_naam_conform_conventie',
            'relatie_drager_naar_toestel_aanwezig',
            'LED_toestel_1_uuid', 'LED_toestel_1_naam', 'LED_toestel_1_naam_conform_conventie',
            'relatie_naar_armatuur_controller_1_aanwezig',
            'armatuur_controller_1_uuid', 'armatuur_controller_1_naam', 'armatuur_controller_1_naam_conform_conventie',
            'legacy_drager_en_drager_binnen_5_meter',
            'legacy_drager_en_drager_identieke_geometrie', 'update_legacy_drager_geometrie',
            'legacy_drager_en_drager_gelijke_toestand', 'update_legacy_drager_toestand',
            'attributen_gelijk', 'update_legacy_drager_attributen'],
        'index': [0, 0],
        'data': [
            ['01', 'DA-01', '00000000-0000-0000-0000-000000000008', 'VPLMast',
             'A0000/A0000.WV/A01', True,  # 'legacy_drager_naampad', 'legacy_drager_naampad_conform_conventie',
             True, True,  # 'drager_verwacht', 'relatie_legacy_naar_drager_aanwezig',
             # 'drager_uuid', 'drager_type', 'drager_naam', 'drager_naam_conform_conventie',
             '00000000-0000-0000-0000-000000000004', 'WVLichtmast', 'A0000.A01', True,
             True,  # 'relatie_drager_naar_toestel_aanwezig',
             # 'LED_toestel_1_uuid', 'LED_toestel_1_naam', 'LED_toestel_1_naam_conform_conventie',
             '00000000-0000-0000-0000-000000000002', 'A0000.A01.WV1', True,
             True,  # 'relatie_naar_armatuur_controller_1_aanwezig',
             # 'armatuur_controller_1_uuid', 'armatuur_controller_1_naam', 'armatuur_controller_1_naam_conform_conventie'
             '00000000-0000-0000-0000-000000000006', 'A0000.A01.WV1.AC1', True,
             True,
             False, '',
             True, '',
             True, ''],
            ['01', 'DA-01', '00000000-0000-0000-0000-000000000009', 'VPConsole',
             'A0000/A0000.WV/C02', True,  # 'legacy_drager_naampad', 'legacy_drager_naampad_conform_conventie',
             True, True,  # 'drager_verwacht', 'relatie_legacy_naar_drager_aanwezig',
             # 'drager_uuid', 'drager_type', 'drager_naam', 'drager_naam_conform_conventie',
             '00000000-0000-0000-0000-000000000005', 'WVConsole', 'A0000.FOUT1', False,
             True,  # 'relatie_drager_naar_toestel_aanwezig',
             # 'LED_toestel_1_uuid', 'LED_toestel_1_naam', 'LED_toestel_1_naam_conform_conventie',
             '00000000-0000-0000-0000-000000000003', 'A0000.C02.WV1', True,
             True,  # 'relatie_naar_armatuur_controller_1_aanwezig',
             # 'armatuur_controller_1_uuid', 'armatuur_controller_1_naam', 'armatuur_controller_1_naam_conform_conventie'
             '00000000-0000-0000-0000-000000000007', 'A0000.C02.WV1.AC1', True,
             False,
             False,
             '',
             False,
             'uit-gebruik',
             False,
             '{\n'
             '    "aantal_te_verlichten_rijvakken_LED": null,\n'
             '    "datum_installatie_LED": null,\n'
             '    "kleurtemperatuur_LED": null,\n'
             '    "lichtpunthoogte_tov_rijweg": null,\n'
             '    "lumen_pakket_LED": null,\n'
             '    "overhang_LED": null,\n'
             '    "verlichtingsniveau_LED": null,\n'
             '    "verlichtingstoestel_merk_en_type": null,\n'
             '    "verlichtingstoestel_systeemvermogen": null,\n'
             '    "verlichtingstype": null\n'
             '}']]}

    report = collector.start_creating_report('01', 'DA-01')
    report = report.iloc[:, :-21]

    assert report.to_dict('split') == expected_report


def test_is_conform_name_convention_toestel():
    assert AssetInfoCollector.is_conform_name_convention_toestel(
        toestel_name='A0000.A01.WV1', installatie_nummer='A0000', lichtpunt_nummer='A01', toestel_index=1)
    assert AssetInfoCollector.is_conform_name_convention_toestel(
        toestel_name='A0002.A02.WV2', installatie_nummer='A0002', lichtpunt_nummer='A02', toestel_index=2)
    assert not AssetInfoCollector.is_conform_name_convention_toestel(
        toestel_name='A0000.A01.WV1', installatie_nummer='A0000', lichtpunt_nummer='A01', toestel_index=2)
    assert not AssetInfoCollector.is_conform_name_convention_toestel(
        toestel_name='A0000.A01.WV2', installatie_nummer='A0000', lichtpunt_nummer='A02', toestel_index=1)
    assert not AssetInfoCollector.is_conform_name_convention_toestel(
        toestel_name='A0001.A01.WV1', installatie_nummer='A0000', lichtpunt_nummer='A01', toestel_index=1)
    assert not AssetInfoCollector.is_conform_name_convention_toestel(
        toestel_name='A0000.A01.WV1.AC1', installatie_nummer='A0000', lichtpunt_nummer='A01', toestel_index=1)
    assert not AssetInfoCollector.is_conform_name_convention_toestel(
        toestel_name='A0000.A01.WV', installatie_nummer='A0000', lichtpunt_nummer='A01', toestel_index=1)


def test_is_conform_name_convention_armatuur_controller():
    assert AssetInfoCollector.is_conform_name_convention_armatuur_controller(
        controller_name='A0000.A01.WV1.AC1', toestel_name='A0000.A01.WV1')
    assert AssetInfoCollector.is_conform_name_convention_armatuur_controller(
        controller_name='A0000.A01.WV2.AC1', toestel_name='A0000.A01.WV2')
    assert not AssetInfoCollector.is_conform_name_convention_armatuur_controller(
        controller_name='A0000.A01.AC1', toestel_name='A0000.A01.WV1')
    assert not AssetInfoCollector.is_conform_name_convention_armatuur_controller(
        controller_name='A0000.A01.WV1', toestel_name='A0000.A01.WV1.AC1')
    assert not AssetInfoCollector.is_conform_name_convention_armatuur_controller(
        controller_name='A0000.A01.WV2.AC1', toestel_name='A0000.A01.WV1')


def test_is_conform_name_convention_drager():
    assert AssetInfoCollector.is_conform_name_convention_drager(
        drager_name='A0000.A01', installatie_nummer='A0000', lichtpunt_nummer='A01')
    assert AssetInfoCollector.is_conform_name_convention_drager(
        drager_name='A0001.A02', installatie_nummer='A0001', lichtpunt_nummer='A02')
    assert not AssetInfoCollector.is_conform_name_convention_drager(
        drager_name='A0000.A01.WV1', installatie_nummer='A0000', lichtpunt_nummer='A01')
    assert not AssetInfoCollector.is_conform_name_convention_drager(
        drager_name='A0000.A01.WV1.AC1', installatie_nummer='A0000', lichtpunt_nummer='A01')
    assert not AssetInfoCollector.is_conform_name_convention_drager(
        drager_name='A0000.A02', installatie_nummer='A0001', lichtpunt_nummer='A02')


def test_is_conform_name_convention_legacy_drager():
    assert AssetInfoCollector.is_conform_name_convention_legacy_drager(
        legacy_drager_naampad='A0000/A0000.WV/A01', installatie_nummer='A0000', lichtpunt_nummer='A01')
    assert AssetInfoCollector.is_conform_name_convention_legacy_drager(
        legacy_drager_naampad='A0001/A0001.WV/A02', installatie_nummer='A0001', lichtpunt_nummer='A02')
    assert not AssetInfoCollector.is_conform_name_convention_legacy_drager(
        legacy_drager_naampad='A0002/A0002.WV/A02', installatie_nummer='A0001', lichtpunt_nummer='A02')
    assert not AssetInfoCollector.is_conform_name_convention_legacy_drager(
        legacy_drager_naampad='A0001/A0001.WV/A02', installatie_nummer='A0001', lichtpunt_nummer='A01')
    assert not AssetInfoCollector.is_conform_name_convention_legacy_drager(
        legacy_drager_naampad='A00002/A0002.WV/A02', installatie_nummer='A00002', lichtpunt_nummer='A02')


def test_get_installatie_nummer_from_naampad():
    assert AssetInfoCollector.get_installatie_nummer_from_naampad('A0000/A0000.WV/A01') == 'A0000'
    assert AssetInfoCollector.get_installatie_nummer_from_naampad('0000/A0000.WV/A01') == '0000'
    assert AssetInfoCollector.get_installatie_nummer_from_naampad('A0000/A0000.WV/101') == 'A0000'
    assert AssetInfoCollector.get_installatie_nummer_from_naampad('A0000') == ''
    assert AssetInfoCollector.get_installatie_nummer_from_naampad('') == ''
    assert AssetInfoCollector.get_installatie_nummer_from_naampad(None) == ''


def test_get_installatie_nummer_from_toestel_name():
    assert AssetInfoCollector.get_installatie_nummer_from_toestel_name('A0000.A01.WV1') == 'A0000'
    assert AssetInfoCollector.get_installatie_nummer_from_toestel_name('0000.A01.WV1') == '0000'
    assert AssetInfoCollector.get_installatie_nummer_from_toestel_name('A0000.A01.WV1.AC1') == 'A0000'
    assert AssetInfoCollector.get_installatie_nummer_from_toestel_name('A0000') == ''
    assert AssetInfoCollector.get_installatie_nummer_from_toestel_name('') == ''
    assert AssetInfoCollector.get_installatie_nummer_from_toestel_name(None) == ''


def test_get_lichtpunt_nummer_from_toestel_name():
    assert AssetInfoCollector.get_lichtpunt_nummer_from_toestel_name('A0000.A01.WV1') == 'A01'
    assert AssetInfoCollector.get_lichtpunt_nummer_from_toestel_name('0000.01.WV1') == '01'
    assert AssetInfoCollector.get_lichtpunt_nummer_from_toestel_name('A0000.A01.WV1.AC1') == 'A01'
    assert AssetInfoCollector.get_lichtpunt_nummer_from_toestel_name('A0000') == ''
    assert AssetInfoCollector.get_lichtpunt_nummer_from_toestel_name('') == ''
    assert AssetInfoCollector.get_lichtpunt_nummer_from_toestel_name(None) == ''


@pytest.mark.parametrize("value, expected", [
    ('https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedOverhang/1-0', 'O+1'),
    ('https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedOverhang/1-0-2', 'O-1'),
    ('https://wegenenverkeer.data.vlaanderen.be/id/concept/KlWvLedOverhang/0-2', '0'),
])
def test_map_overhang(value, expected):
    assert AssetInfoCollector.map_overhang(value) == expected


def test_distance_between_drager_and_legacy_drager():
    fake_requester = Mock(spec=AbstractRequester)
    fake_requester.first_part_url = ''
    AssetInfoCollector.create_requester_with_settings = Mock(return_value=fake_requester)
    collector = AssetInfoCollector(auth_type=Mock(), env=Mock(), settings_path=Mock())
    collector.em_infra_importer = fake_em_infra_importer

    collector.collect_asset_info(uuids=['00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000008',
                                        '00000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000009'])

    drager_node_1 = deepcopy(collector.collection.get_node_object_by_uuid('00000000-0000-0000-0000-000000000004'))
    legacy_drager_node_1 = deepcopy(
        collector.collection.get_node_object_by_uuid('00000000-0000-0000-0000-000000000008'))
    drager_node_2 = collector.collection.get_node_object_by_uuid('00000000-0000-0000-0000-000000000005')
    legacy_drager_node_2 = collector.collection.get_node_object_by_uuid('00000000-0000-0000-0000-000000000009')

    assert AssetInfoCollector.distance_between_drager_and_legacy_drager(
        drager=None, legacy_drager=None) == 100.0

    assert AssetInfoCollector.distance_between_drager_and_legacy_drager(
        drager=drager_node_2, legacy_drager=legacy_drager_node_2) == 100.0

    assert AssetInfoCollector.distance_between_drager_and_legacy_drager(
        drager=drager_node_1, legacy_drager=legacy_drager_node_1) == 1.0

    drager_node_1.attr_dict['geo:Geometrie.log'][0]['geo:DtcLog.geometrie'][
        'geo:DtuGeometrie.punt'] = 'POINT Z (200005.0 200004.0 0)'

    assert AssetInfoCollector.distance_between_drager_and_legacy_drager(
        drager=drager_node_1, legacy_drager=legacy_drager_node_1) == 5.0

    del drager_node_1.attr_dict['geo:Geometrie.log'][0]['geo:DtcLog.geometrie']['geo:DtuGeometrie.punt']

    assert AssetInfoCollector.distance_between_drager_and_legacy_drager(
        drager=drager_node_1, legacy_drager=legacy_drager_node_1) == 100.0

    del drager_node_1.attr_dict['geo:Geometrie.log'][0]['geo:DtcLog.geometrie']

    assert AssetInfoCollector.distance_between_drager_and_legacy_drager(
        drager=drager_node_1, legacy_drager=legacy_drager_node_1) == 100.0

    del drager_node_1.attr_dict['geo:Geometrie.log'][0]

    assert AssetInfoCollector.distance_between_drager_and_legacy_drager(
        drager=drager_node_1, legacy_drager=legacy_drager_node_1) == 100.0

    del drager_node_1.attr_dict['geo:Geometrie.log']

    assert AssetInfoCollector.distance_between_drager_and_legacy_drager(
        drager=drager_node_1, legacy_drager=legacy_drager_node_1) == 100.0

    del legacy_drager_node_1.attr_dict['loc:Locatie.puntlocatie']['loc:3Dpunt.puntgeometrie'][
        'loc:DtcCoord.lambert72']['loc:DtcCoordLambert72.xcoordinaat']

    assert AssetInfoCollector.distance_between_drager_and_legacy_drager(
        drager=drager_node_1, legacy_drager=legacy_drager_node_1) == 100.0

    del legacy_drager_node_1.attr_dict['loc:Locatie.puntlocatie']['loc:3Dpunt.puntgeometrie']['loc:DtcCoord.lambert72']

    assert AssetInfoCollector.distance_between_drager_and_legacy_drager(
        drager=drager_node_1, legacy_drager=legacy_drager_node_1) == 100.0

    del legacy_drager_node_1.attr_dict['loc:Locatie.puntlocatie']['loc:3Dpunt.puntgeometrie']

    assert AssetInfoCollector.distance_between_drager_and_legacy_drager(
        drager=drager_node_1, legacy_drager=legacy_drager_node_1) == 100.0

    del legacy_drager_node_1.attr_dict['loc:Locatie.puntlocatie']

    assert AssetInfoCollector.distance_between_drager_and_legacy_drager(
        drager=drager_node_1, legacy_drager=legacy_drager_node_1) == 100.0


def test_get_attribute_dict_from_legacy_drager():
    fake_requester = Mock(spec=AbstractRequester)
    fake_requester.first_part_url = ''
    AssetInfoCollector.create_requester_with_settings = Mock(return_value=fake_requester)
    collector = AssetInfoCollector(auth_type=Mock(), env=Mock(), settings_path=Mock())
    collector.em_infra_importer = fake_em_infra_importer

    collector.collect_asset_info(uuids=['00000000-0000-0000-0000-000000000008', '00000000-0000-0000-0000-000000000009'])
    legacy_drager_node_1 = collector.collection.get_node_object_by_uuid('00000000-0000-0000-0000-000000000008')
    legacy_drager_node_2 = collector.collection.get_node_object_by_uuid('00000000-0000-0000-0000-000000000009')

    d_1 = AssetInfoCollector.get_attribute_dict_from_legacy_drager(legacy_drager=legacy_drager_node_1)
    d_2 = AssetInfoCollector.get_attribute_dict_from_legacy_drager(legacy_drager=legacy_drager_node_2)

    assert d_1 == {
        'aantal_te_verlichten_rijvakken_LED': 'R1',
        'aantal_verlichtingstoestellen': 4,
        'contractnummer_levering_LED': '123456',
        'datum_installatie_LED': '2020-01-01',
        'kleurtemperatuur_LED': 'K3000',
        'LED_verlichting': True,
        'drager_buiten_gebruik': False,
        'lichtpunthoogte_tov_rijweg': 6,
        'lumen_pakket_LED': 10000,
        'overhang_LED': 'O+1',
        'RAL_kleur': '7038',
        'serienummer_armatuurcontroller_1': '1234561',
        'serienummer_armatuurcontroller_2': '1234562',
        'serienummer_armatuurcontroller_3': '1234563',
        'serienummer_armatuurcontroller_4': '1234564',
        'verlichtingsniveau_LED': 'M3',
        'verlichtingstoestel_merk_en_type': 'Schreder Ampera',
        'verlichtingstoestel_systeemvermogen': 100,
        'verlichtingstype': 'hoofdbaan'
    }
    assert d_2 == {
        'aantal_te_verlichten_rijvakken_LED': 'R2',
        'aantal_verlichtingstoestellen': 1,
        'contractnummer_levering_LED': '123456',
        'datum_installatie_LED': '2020-01-01',
        'kleurtemperatuur_LED': 'K3000',
        'LED_verlichting': True,
        'drager_buiten_gebruik': False,
        'lichtpunthoogte_tov_rijweg': 5,
        'lumen_pakket_LED': 10000,
        'overhang_LED': '0',
        'RAL_kleur': '7038',
        'serienummer_armatuurcontroller_1': '1234561',
        'verlichtingsniveau_LED': 'M2',
        'verlichtingstoestel_merk_en_type': 'Schreder Ampera',
        'verlichtingstoestel_systeemvermogen': 100,
        'verlichtingstype': 'hoofdbaan'
    }


def test_get_attribute_dict_from_drager():
    fake_requester = Mock(spec=AbstractRequester)
    fake_requester.first_part_url = ''
    AssetInfoCollector.create_requester_with_settings = Mock(return_value=fake_requester)
    collector = AssetInfoCollector(auth_type=Mock(), env=Mock(), settings_path=Mock())
    collector.em_infra_importer = fake_em_infra_importer

    collector.collect_asset_info(uuids=['00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000002',
                                        '00000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000022',
                                        '00000000-0000-0000-0000-000000000023', '00000000-0000-0000-0000-000000000024',
                                        '00000000-0000-0000-0000-000000000026'])
    drager = collector.collection.get_node_object_by_uuid('00000000-0000-0000-0000-000000000004')
    toestellen = collector.collection.get_node_objects_by_types(['onderdeel#VerlichtingstoestelLED'])
    armatuur_controllers = collector.collection.get_node_objects_by_types(['onderdeel#Armatuurcontroller'])

    d_1 = AssetInfoCollector.get_attribute_dict_from_otl_assets(drager=drager, toestellen=list(toestellen),
                                                                armatuur_controllers=list(armatuur_controllers))

    d_expected = {
        'contractnummer_levering_LED': '123456',
        'drager_buiten_gebruik': False,
    }

    d_expected = {
        'aantal_verlichtingstoestellen': 4,
        'aantal_te_verlichten_rijvakken_LED': 'R1',
        'datum_installatie_LED': '2020-01-01',
        'kleurtemperatuur_LED': 'K3000',
        'LED_verlichting': True,
        'lichtpunthoogte_tov_rijweg': 6,
        'lumen_pakket_LED': 10000,
        'overhang_LED': 'O+1',
        'RAL_kleur': '7038',
        'serienummer_armatuurcontroller_1': '1234561',
        'serienummer_armatuurcontroller_2': '1234562',
        'verlichtingsniveau_LED': 'M3',
        'verlichtingstoestel_merk_en_type': 'Schreder Ampera',
        'verlichtingstoestel_systeemvermogen': 100,
        'verlichtingstype': 'hoofdbaan'
    }

    assert  d_1 == d_expected


def node_info_object_mock(verlichtingstype_value):
    node_info_object = Mock(spec=NodeInfoObject)
    node_info_object.attr_dict = {
        'Verlichtingstoestel.verlichtGebied':
            'https://wegenenverkeer.data.vlaanderen.be/id/concept/KlVerlichtingstoestelVerlichtGebied/' +
            verlichtingstype_value}
    return node_info_object


def test_get_verlichtingstype():
    toestellen = [node_info_object_mock('hoofdweg'), node_info_object_mock('hoofdweg')]
    assert AssetInfoCollector.get_verlichtingstype(toestellen) == 'hoofdbaan'
    toestellen = [node_info_object_mock('hoofdweg'), node_info_object_mock('fietspad')]
    assert AssetInfoCollector.get_verlichtingstype(toestellen) == 'hoofdbaan'
    toestellen = [node_info_object_mock('fietspad'), node_info_object_mock('fietspad')]
    assert AssetInfoCollector.get_verlichtingstype(toestellen) == 'fietspadverlichting'
    toestellen = [node_info_object_mock('hoofdweg'), node_info_object_mock('fietspad'),
                  node_info_object_mock('hoofdweg'), node_info_object_mock('fietspad')]
    assert AssetInfoCollector.get_verlichtingstype(toestellen) == 'hoofdbaan'
    toestellen = [node_info_object_mock('hoofdweg'), node_info_object_mock('afrit')]
    assert AssetInfoCollector.get_verlichtingstype(toestellen) == 'opafrit'
