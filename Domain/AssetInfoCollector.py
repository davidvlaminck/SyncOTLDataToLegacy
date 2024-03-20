import json
import logging
import math
import re
from pathlib import Path
from typing import Generator

from API.AbstractRequester import AbstractRequester
from Domain.AssetCollection import AssetCollection
from API.EMInfraRestClient import EMInfraRestClient
from API.EMsonImporter import EMsonImporter
from Domain.Enums import AuthType, Environment, Direction
from Domain.InfoObject import NodeInfoObject
from Exceptions.AssetsMissingError import AssetsMissingError
from Exceptions.ObjectAlreadyExistsError import ObjectAlreadyExistsError
from API.RequesterFactory import RequesterFactory
from pandas import DataFrame, concat


class AssetInfoCollector:
    def __init__(self, settings_path: Path, auth_type: AuthType, env: Environment):
        self.em_infra_importer = EMInfraRestClient(self.create_requester_with_settings(
            settings_path=settings_path, auth_type=auth_type, env=env))
        self.emson_importer = EMsonImporter(self.create_requester_with_settings(
            settings_path=settings_path, auth_type=auth_type, env=env))
        self.collection = AssetCollection()

    @classmethod
    def create_requester_with_settings(cls, settings_path: Path, auth_type: AuthType, env: Environment
                                       ) -> AbstractRequester:
        with open(settings_path) as settings_file:
            settings = json.load(settings_file)
        return RequesterFactory.create_requester(settings=settings, auth_type=auth_type, env=env)

    def get_assets_by_uuids(self, uuids: [str]) -> Generator[dict, None, None]:
        return self.em_infra_importer.get_objects_from_oslo_search_endpoint_using_iterator(resource='assets',
                                                                                           filter_dict={'uuid': uuids})
        # return self.emson_importer.get_assets_by_uuid_using_iterator(uuids=uuids)

    def get_assetrelaties_by_uuids(self, uuids: [str]) -> Generator[dict, None, None]:
        return self.em_infra_importer.get_objects_from_oslo_search_endpoint_using_iterator(resource='assetrelaties',
                                                                                           filter_dict={'uuid': uuids})

    def get_assetrelaties_by_source_or_target_uuids(self, uuids: [str]) -> Generator[dict, None, None]:
        return self.em_infra_importer.get_objects_from_oslo_search_endpoint_using_iterator(resource='assetrelaties',
                                                                                           filter_dict={'asset': uuids})

    def collect_asset_info(self, uuids: [str]) -> None:
        for asset in self.get_assets_by_uuids(uuids=uuids):
            asset['uuid'] = asset.pop('@id')[39:75]
            asset['typeURI'] = asset.pop('@type')
            self.collection.add_node(asset)

    def _common_collect_relation_info(self, assetrelaties_generator: Generator[dict, None, None],
                                      ignore_duplicates: bool = False) -> None:
        asset_missing_error = AssetsMissingError(msg='')
        for relation in assetrelaties_generator:
            relation['uuid'] = relation.pop('@id')[46:82]
            relation['typeURI'] = relation.pop('@type')
            relation['bron'] = relation['RelatieObject.bron']['@id'][39:75]
            relation['doel'] = relation['RelatieObject.doel']['@id'][39:75]
            try:
                self.collection.add_relation(relation)
            except AssetsMissingError as e:
                asset_missing_error.uuids.extend(e.uuids)
                asset_missing_error.msg += e.msg
            except ObjectAlreadyExistsError as e:
                if not ignore_duplicates:
                    raise e
        if asset_missing_error.uuids:
            raise asset_missing_error

    def collect_relation_info(self, uuids: [str], ignore_duplicates: bool = False) -> None:
        self._common_collect_relation_info(self.get_assetrelaties_by_uuids(uuids=uuids),
                                           ignore_duplicates=ignore_duplicates)

    def collect_relation_info_by_sources_or_targets(self, uuids: [str], ignore_duplicates: bool = False) -> None:
        self._common_collect_relation_info(self.get_assetrelaties_by_source_or_target_uuids(uuids=uuids),
                                           ignore_duplicates=ignore_duplicates)

    def start_collecting_from_starting_uuids(self, starting_uuids: [str]) -> None:
        # deprecated
        self.collect_asset_info(uuids=starting_uuids)

        # hardcoded pattern
        # bevestiging verlichtingstoestelLED > console, mast, armatuur
        # console + mast
        # hoort_bij > legacy mast/console

        toestellen = self.collection.get_node_objects_by_types(['onderdeel#VerlichtingstoestelLED'])
        toestel_uuids = [toestel.uuid for toestel in toestellen]
        try:
            self.collect_relation_info_by_sources_or_targets(uuids=toestel_uuids, ignore_duplicates=True)
        except AssetsMissingError as e:
            self.collect_asset_info(uuids=e.uuids)
            self.collect_relation_info_by_sources_or_targets(uuids=toestel_uuids, ignore_duplicates=True)

        dragers = self.collection.get_node_objects_by_types(['onderdeel#WVLichtmast', 'onderdeel#WVConsole',
                                                             'onderdeel#PunctueleVerlichtingsmast'])
        drager_uuids = [drager.uuid for drager in dragers]
        try:
            self.collect_relation_info_by_sources_or_targets(uuids=drager_uuids, ignore_duplicates=True)
        except AssetsMissingError as e:
            self.collect_asset_info(uuids=e.uuids)
            self.collect_relation_info_by_sources_or_targets(uuids=drager_uuids, ignore_duplicates=True)

    def start_collecting_from_starting_uuids_using_pattern(self, starting_uuids: [str],
                                                           pattern: [tuple[str, str, object]]) -> None:
        uuid_pattern = next((t[2] for t in pattern if t[:2] == ('uuids', 'of')), None)
        type_of_patterns = [t for t in pattern if t[1] == 'type_of']
        relation_patterns = [t for t in pattern if re.match('^(<)?-\\[r(\\d)*]-(>)?$', t[1]) is not None]

        if uuid_pattern is None:
            raise ValueError('No uuids pattern found in pattern list. '
                             'Must contain one tuple with ("uuids", "of", object)')
        if not type_of_patterns:
            raise ValueError('No type_of pattern found in pattern list. '
                             'Must contain at least one tuple with (object, "type_of", object)')
        if not relation_patterns:
            raise ValueError('No relation pattern found in pattern list'
                             'Must contain at least one tuple with (object, "-[r]-", object) where r is followed by a '
                             'number and relation may or may not be directional (using < and > symbols)')

        self.collect_asset_info(uuids=starting_uuids)

        matching_objects = [uuid_pattern]
        while relation_patterns:
            new_matching_objects = []
            for obj in matching_objects:
                relation_patterns = self.order_patterns_for_object(obj, relation_patterns)

                for relation_pattern in relation_patterns:
                    if relation_pattern[0] != obj:
                        continue

                    new_matching_objects.append(relation_pattern[2])

                    type_of_obj = next((t[2] for t in type_of_patterns if t[0] == relation_pattern[0]), None)
                    if type_of_obj is None:
                        raise ValueError(f'No type_of pattern found for object {relation_pattern[0]}')

                    type_of_uuids = [asset.uuid for asset in self.collection.get_node_objects_by_types(type_of_obj)]
                    if not type_of_uuids:
                        continue
                    try:
                        self.collect_relation_info_by_sources_or_targets(uuids=type_of_uuids, ignore_duplicates=True)
                    except AssetsMissingError as e:
                        self.collect_asset_info(uuids=e.uuids)
                        self.collect_relation_info_by_sources_or_targets(uuids=type_of_uuids, ignore_duplicates=True)

                relation_patterns = [t for t in relation_patterns if t[0] != obj]
            matching_objects = new_matching_objects

    def start_creating_report(self, aanlevering_id: str, aanlevering_naam: str) -> DataFrame:
        df = DataFrame()
        all_column_names = [
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
            'attributen_gelijk', 'update_legacy_drager_attributen',
            'LED_toestel_2_uuid', 'LED_toestel_2_naam', 'LED_toestel_2_naam_conform_conventie',
            'LED_toestel_3_uuid', 'LED_toestel_3_naam', 'LED_toestel_3_naam_conform_conventie',
            'LED_toestel_4_uuid', 'LED_toestel_4_naam', 'LED_toestel_4_naam_conform_conventie',
            'relatie_naar_armatuur_controller_2_aanwezig',
            'armatuur_controller_2_uuid', 'armatuur_controller_2_naam', 'armatuur_controller_2_naam_conform_conventie',
            'relatie_naar_armatuur_controller_3_aanwezig',
            'armatuur_controller_3_uuid', 'armatuur_controller_3_naam', 'armatuur_controller_3_naam_conform_conventie',
            'relatie_naar_armatuur_controller_4_aanwezig',
            'armatuur_controller_4_uuid', 'armatuur_controller_4_naam', 'armatuur_controller_4_naam_conform_conventie']
        for missing_column_name in all_column_names:
            df[missing_column_name] = None

        # get all legacy dragers
        dragers = self.collection.get_node_objects_by_types([
            'lgc:installatie#VPLMast', 'lgc:installatie#VPConsole', 'lgc:installatie#VPBevestig'])

        for drager in dragers:
            legacy_drager_uuid = drager.uuid
            legacy_drager_naampad = drager.attr_dict.get('NaampadObject.naampad', '')
            legacy_drager_type = drager.short_type.split('#')[-1]
            current_lgc_drager_dict = {
                'aanlevering_id': [aanlevering_id], 'aanlevering_naam': [aanlevering_naam],
                'legacy_drager_uuid': legacy_drager_uuid, 'legacy_drager_naampad': legacy_drager_naampad,
                'legacy_drager_type': legacy_drager_type
            }

            record_dict = self.get_report_record_for_one_lgc_drager(lgc_drager=drager,
                                                                    record_dict=current_lgc_drager_dict)
            df_current = DataFrame(record_dict)
            df = concat([df, df_current])

        return df.sort_values('legacy_drager_uuid')

    @classmethod
    def order_patterns_for_object(cls, obj: str, relation_patterns: [tuple[str, str, str]]) -> [tuple[str, str, str]]:
        ordered_patterns = []
        for relation_pattern in relation_patterns:
            if relation_pattern[2] == obj:
                ordered_patterns.append(AssetInfoCollector.reverse_relation_pattern(relation_pattern))
            else:
                ordered_patterns.append(relation_pattern)
        return ordered_patterns

    @classmethod
    def reverse_relation_pattern(cls, relation_pattern: tuple[str, str, str]) -> tuple[str, str, str]:
        rel_str = relation_pattern[1]
        parts = re.match('(<?-)\\[(r.+)](->?)', rel_str).groups()
        parts_2 = parts[0].replace('<', '>')[::-1]
        parts_0 = parts[2].replace('>', '<')[::-1]

        return relation_pattern[2], f'{parts_0}[{parts[1]}]{parts_2}', relation_pattern[0]

    def print_feed_page(self):
        self.em_infra_importer.print_feed_page()

    def get_report_record_for_one_lgc_drager(self, lgc_drager: NodeInfoObject, record_dict: dict) -> dict:
        legacy_drager_uuid = record_dict['legacy_drager_uuid']
        legacy_drager_naampad = record_dict['legacy_drager_naampad']
        legacy_drager_type = record_dict['legacy_drager_type']

        installatie_nummer = self.get_installatie_nummer_from_naampad(naampad=legacy_drager_naampad)
        lichtpunt_nummer = self.get_lichtpunt_nummer_from_naampad(naampad=legacy_drager_naampad)
        record_dict['legacy_drager_naampad_conform_conventie'] = (
            self.is_conform_name_convention_legacy_drager(
                legacy_drager_naampad=legacy_drager_naampad, installatie_nummer=installatie_nummer,
                lichtpunt_nummer=lichtpunt_nummer))

        record_dict['drager_verwacht'] = [legacy_drager_type != 'VPBevestig']

        toestellen: [str | NodeInfoObject]
        if record_dict['drager_verwacht'][0]:
            dragers = list(self.collection.traverse_graph(
                start_uuid=legacy_drager_uuid, relation_types=['HoortBij'], allowed_directions=[Direction.REVERSED],
                return_type='info_object', filtered_node_types=['onderdeel#WVLichtmast', 'onderdeel#WVConsole',
                                                                'onderdeel#PunctueleVerlichtingsmast']))
            if not dragers:
                logging.info(f"{legacy_drager_naampad} heeft geen HoortBij relatie naar een drager")
                record_dict['relatie_legacy_naar_drager_aanwezig'] = [False]
                return record_dict

            drager = dragers[0]
            drager_uuid = drager.uuid
            drager_naam = drager.attr_dict.get('AIMNaamObject.naam', '')
            record_dict['relatie_legacy_naar_drager_aanwezig'] = [True]
            record_dict['drager_uuid'] = [drager.uuid]
            record_dict['drager_type'] = [drager.short_type.split('#')[-1]]
            record_dict['drager_naam'] = [drager_naam]
            record_dict['drager_naam_conform_conventie'] = (
                self.is_conform_name_convention_drager(drager_name=drager_naam, installatie_nummer=installatie_nummer,
                                                       lichtpunt_nummer=lichtpunt_nummer))

            toestellen = list(self.collection.traverse_graph(
                start_uuid=drager_uuid, relation_types=['Bevestiging'], allowed_directions=[Direction.NONE],
                return_type='info_object', filtered_node_types=['onderdeel#VerlichtingstoestelLED']))
            if not toestellen:
                if drager_naam == '':
                    drager_naam = drager_uuid
                logging.info(
                    f"drager {drager_naam} van {legacy_drager_naampad} heeft geen relatie naar een LED toestel")
                record_dict['relatie_drager_naar_toestel_aanwezig'] = [False]
                return record_dict
        else:
            toestellen = list(self.collection.traverse_graph(
                start_uuid=legacy_drager_uuid, relation_types=['HoortBij'], allowed_directions=[Direction.REVERSED],
                return_type='info_object', filtered_node_types=['onderdeel#VerlichtingstoestelLED']))
            if not toestellen:
                logging.info(f"{legacy_drager_naampad} heeft geen HoortBij relatie naar een LED toestel")
                record_dict['relatie_drager_naar_toestel_aanwezig'] = [False]
                return record_dict

        record_dict['relatie_drager_naar_toestel_aanwezig'] = [True]
        toestellen_new = sorted(toestellen, key=lambda t: t.attr_dict.get('AIMNaamObject.naam', ''))
        armatuur_controllers = []

        for index, toestel in enumerate(toestellen_new):
            toestel_index = index + 1
            toestel_uuid = toestel.uuid
            toestel_name = toestel.attr_dict.get('AIMNaamObject.naam', '')
            record_dict[f'LED_toestel_{toestel_index}_uuid'] = [toestel_uuid]
            record_dict[f'LED_toestel_{toestel_index}_naam'] = [toestel_name]
            record_dict[
                f'LED_toestel_{toestel_index}_naam_conform_conventie'] = self.is_conform_name_convention_toestel(
                toestel_name=toestel_name, installatie_nummer=installatie_nummer, lichtpunt_nummer=lichtpunt_nummer,
                toestel_index=toestel_index)

            controllers = list(self.collection.traverse_graph(
                start_uuid=toestel_uuid, relation_types=['Bevestiging'], allowed_directions=[Direction.NONE],
                return_type='info_object', filtered_node_types=['onderdeel#Armatuurcontroller']))

            if not controllers:
                logging.info(f"toestel {toestel_index} van {legacy_drager_naampad} heeft geen relatie "
                             f"naar een armatuur controller")
                record_dict[f'relatie_naar_armatuur_controller_{toestel_index}_aanwezig'] = [False]
            else:
                controller = controllers[0]
                armatuur_controllers.append(controller)
                record_dict[f'relatie_naar_armatuur_controller_{toestel_index}_aanwezig'] = [True]
                record_dict[f'armatuur_controller_{toestel_index}_uuid'] = [controller.uuid]
                controller_name = controller.attr_dict.get('AIMNaamObject.naam', '')
                record_dict[f'armatuur_controller_{toestel_index}_naam'] = [controller_name]
                record_dict[f'armatuur_controller_{toestel_index}_naam_conform_conventie'] = (
                    self.is_conform_name_convention_armatuur_controller(
                        controller_name=controller_name, toestel_name=toestel_name))

        if drager:
            # geometry
            distance = self.distance_between_drager_and_legacy_drager(legacy_drager=lgc_drager, drager=drager)
            record_dict['legacy_drager_en_drager_binnen_5_meter'] = [distance <= 5.0]
            record_dict['legacy_drager_en_drager_identieke_geometrie'] = [0.0 < distance <= 0.01]
            record_dict['update_legacy_drager_geometrie'] = ''  # TODO: change to legacy geometry for legacy_drager

            # toestand
            legacy_drager_toestand = lgc_drager.attr_dict.get('AIMToestand.toestand')
            drager_toestand = drager.attr_dict.get('AIMToestand.toestand')
            record_dict['legacy_drager_en_drager_gelijke_toestand'] = [legacy_drager_toestand == drager_toestand]
            if record_dict['legacy_drager_en_drager_gelijke_toestand'][0]:
                record_dict['update_legacy_drager_toestand'] = ''
            else:
                record_dict['update_legacy_drager_toestand'] = drager_toestand[67:]

        # bestekkoppeling
        # TODO

        # schadebeheerder
        # TODO

        # toezichter
        # TODO

        # vtc instructie
        # TODO?

        # attributen
        drager_dict = self.get_attribute_dict_from_otl_assets(drager=drager, toestellen=toestellen,
                                                              armatuur_controllers=armatuur_controllers)
        legacy_drager_dict = self.get_attribute_dict_from_legacy_drager(legacy_drager=lgc_drager)
        update_dict = self.get_update_dict(drager_dict=drager_dict, legacy_drager_dict=legacy_drager_dict)
        if update_dict == {}:
            record_dict['attributen_gelijk'] = [True]
            record_dict['update_legacy_drager_attributen'] = ['']
        else:
            record_dict['attributen_gelijk'] = [False]
            record_dict['update_legacy_drager_attributen'] = [json.dumps(update_dict, indent=4)]

        # aantal_te_verlichten_rijvakken_LED
        # aantal_verlichtingstoestellen
        # contractnummer_levering_LED
        # datum_installatie_LED
        # kleurtemperatuur_LED
        # LED_verlichting
        # lichtmast/bevestiging/console_buiten_gebruik
        # lichtpunthoogte_tov_rijweg
        # lumen_pakket_LED
        # overhang_LED
        # RAL_kleur_(VPLMAST/console/VVOP)
        # serienummer_armatuurcontroller_1
        # serienummer_armatuurcontroller_2
        # serienummer_armatuurcontroller_3
        # serienummer_armatuurcontroller_4
        # verlichtingsniveau_LED
        # verlichtingstoestel_merk_en_type
        # verlichtingstoestel_systeemvermogen
        # verlichtingstype

        return record_dict

    @classmethod
    def is_conform_name_convention_toestel(cls, toestel_name: str, installatie_nummer: str,
                                           lichtpunt_nummer: str, toestel_index: int) -> bool:
        return toestel_name == f'{installatie_nummer}.{lichtpunt_nummer}.WV{toestel_index}'

    @classmethod
    def get_installatie_nummer_from_toestel_name(cls, toestel_name: str) -> str:
        if toestel_name is None or not toestel_name or '.' not in toestel_name:
            return ''
        return toestel_name.split('.')[0]

    @classmethod
    def get_installatie_nummer_from_naampad(cls, naampad: str) -> str:
        if naampad is None or not naampad or '/' not in naampad:
            return ''
        return naampad.split('/')[0]

    @classmethod
    def get_lichtpunt_nummer_from_naampad(cls, naampad: str) -> str:
        if naampad is None or not naampad or '/' not in naampad:
            return ''
        return naampad.split('/')[2]

    @classmethod
    def get_lichtpunt_nummer_from_toestel_name(cls, toestel_name: str) -> str:
        if toestel_name is None or not toestel_name or '.' not in toestel_name:
            return ''
        return toestel_name.split('.')[1]

    @classmethod
    def is_conform_name_convention_armatuur_controller(cls, controller_name: str, toestel_name: str) -> bool:
        if controller_name is None or not controller_name:
            return False
        if toestel_name is None or not toestel_name:
            return False
        return controller_name == f'{toestel_name}.AC1'

    @classmethod
    def is_conform_name_convention_drager(cls, drager_name: str, installatie_nummer: str,
                                          lichtpunt_nummer: str) -> bool:
        if drager_name is None or not drager_name:
            return False
        if installatie_nummer is None or not installatie_nummer:
            return False
        if lichtpunt_nummer is None or not lichtpunt_nummer:
            return False
        return drager_name == f'{installatie_nummer}.{lichtpunt_nummer}'

    @classmethod
    def is_conform_name_convention_legacy_drager(cls, legacy_drager_naampad: str, installatie_nummer: str,
                                                 lichtpunt_nummer: str) -> bool:
        if legacy_drager_naampad is None or not legacy_drager_naampad:
            return False
        if installatie_nummer is None or not installatie_nummer:
            return False
        if lichtpunt_nummer is None or not lichtpunt_nummer:
            return False
        if not re.match('^(A|C|G|WO|WW)[0-9]{4}$', installatie_nummer):
            return False
        return legacy_drager_naampad == f'{installatie_nummer}/{installatie_nummer}.WV/{lichtpunt_nummer}'

    @classmethod
    def distance_between_drager_and_legacy_drager(cls, legacy_drager: NodeInfoObject, drager: NodeInfoObject) -> float:
        if legacy_drager is None or drager is None:
            return 100.0
        legacy_puntlocatie = legacy_drager.attr_dict.get('loc:Locatie.puntlocatie')
        if legacy_puntlocatie is None:
            return 100.0
        legacy_puntgeometrie = legacy_puntlocatie.get('loc:3Dpunt.puntgeometrie')
        if legacy_puntgeometrie is None:
            return 100.0
        legacy_coords = legacy_puntgeometrie.get('loc:DtcCoord.lambert72')
        if legacy_coords is None:
            return 100.0
        legacy_x = legacy_coords.get('loc:DtcCoordLambert72.xcoordinaat')
        legacy_y = legacy_coords.get('loc:DtcCoordLambert72.ycoordinaat')
        if legacy_x is None or legacy_y is None:
            return 100.0

        drager_x, drager_y = cls.get_drager_x_y(drager=drager)
        if drager_x is None or drager_y is None:
            return 100.0

        return math.sqrt(abs(legacy_x - drager_x) ** 2 + abs(legacy_y - drager_y) ** 2)

    @classmethod
    def get_drager_x_y(cls, drager: NodeInfoObject) -> (float, float):
        drager_logs = drager.attr_dict.get('geo:Geometrie.log')
        if drager_logs is None:
            return None, None
        if len(drager_logs) == 0:
            return None, None
        log = next((log for log in drager_logs
                    if log.get('geo:DtcLog.niveau') == 'https://geo.data.wegenenverkeer.be/id/concept/KlLogNiveau/0'),
                   None)
        if log is None:
            log = next((log for log in drager_logs
                        if
                        log.get('geo:DtcLog.niveau') == 'https://geo.data.wegenenverkeer.be/id/concept/KlLogNiveau/-1'),
                       None)
        if log is None:
            return None, None
        drager_geometrie = log.get('geo:DtcLog.geometrie')
        if drager_geometrie is None:
            return None, None
        drager_puntgeometrie = drager_geometrie.get('geo:DtuGeometrie.punt')
        if drager_puntgeometrie is None:
            return None, None
        # use regex to get coordinates out of wkt string in drager_puntgeometrie
        drager_coords = re.match(r'POINT Z \((\d+.\d+) (\d+.\d+) (\d+)\)', drager_puntgeometrie)
        if len(drager_coords.groups()) != 3:
            return None, None
        return float(drager_coords[1]), float(drager_coords[2])

    @classmethod
    def get_attribute_dict_from_legacy_drager(cls, legacy_drager: NodeInfoObject) -> dict:
        d = {
            'aantal_te_verlichten_rijvakken_LED': legacy_drager.attr_dict.get(
                'lgc:EMObject.aantalTeVerlichtenRijvakkenLed'),
            'aantal_verlichtingstoestellen': legacy_drager.attr_dict.get('lgc:EMObject.aantalVerlichtingstoestellen'),
            'contractnummer_levering_LED': legacy_drager.attr_dict.get('lgc:EMObject.contractnummerLeveringLed'),
            'datum_installatie_LED': legacy_drager.attr_dict.get('lgc:EMObject.datumInstallatieLed'),
            'kleurtemperatuur_LED': legacy_drager.attr_dict.get('lgc:EMObject.kleurtemperatuurLed'),
            'LED_verlichting': legacy_drager.attr_dict.get('lgc:EMObject.ledVerlichting'),
            'lichtpunthoogte_tov_rijweg': legacy_drager.attr_dict.get('lgc:EMObject.lichtpunthoogteTovRijweg'),
            'lumen_pakket_LED': legacy_drager.attr_dict.get('lgc:EMObject.lumenPakketLed'),
            'overhang_LED': legacy_drager.attr_dict.get('lgc:EMObject.overhangLed'),
            'verlichtingsniveau_LED': legacy_drager.attr_dict.get('lgc:EMObject.verlichtingsniveauLed'),
            'verlichtingstoestel_merk_en_type': legacy_drager.attr_dict.get(
                'lgc:EMObject.verlichtingstoestelMerkEnType'),
            'verlichtingstoestel_systeemvermogen': legacy_drager.attr_dict.get(
                'lgc:EMObject.verlichtingstoestelSysteemvermogen'),
            'verlichtingstype': legacy_drager.attr_dict.get('lgc:EMObject.verlichtingstype')
        }
        if legacy_drager.short_type == 'lgc:installatie#VPLMast':
            d['drager_buiten_gebruik'] = legacy_drager.attr_dict.get('lgc:VPLMast.lichtmastBuitenGebruik')
            d['RAL_kleur'] = legacy_drager.attr_dict.get('lgc:VPLMast.ralKleurVplmast')
            d['serienummer_armatuurcontroller_1'] = legacy_drager.attr_dict.get(
                'lgc:VPLMast.serienummerArmatuurcontroller1')
            d['serienummer_armatuurcontroller_2'] = legacy_drager.attr_dict.get(
                'lgc:VPLMast.serienummerArmatuurcontroller2')
            d['serienummer_armatuurcontroller_3'] = legacy_drager.attr_dict.get(
                'lgc:VPLMast.serienummerArmatuurcontroller3')
            d['serienummer_armatuurcontroller_4'] = legacy_drager.attr_dict.get(
                'lgc:VPLMast.serienummerArmatuurcontroller4')
        elif legacy_drager.short_type == 'lgc:installatie#VPConsole':
            d['drager_buiten_gebruik'] = legacy_drager.attr_dict.get('lgc:VPConsole.consoleBuitenGebruik')
            d['RAL_kleur'] = legacy_drager.attr_dict.get('lgc:VPConsole.ralKleurVpconsole')  # TODO RAL VVOP?
            d['serienummer_armatuurcontroller_1'] = legacy_drager.attr_dict.get(
                'lgc:EMObject.serienummerArmatuurcontroller')
        elif legacy_drager.short_type == 'lgc:installatie#VPBevestig':
            d['drager_buiten_gebruik'] = legacy_drager.attr_dict.get('lgc:VPBevestig.bevestigingBuitenGebruik')
            d['serienummer_armatuurcontroller_1'] = legacy_drager.attr_dict.get(
                'lgc:EMObject.serienummerArmatuurcontroller')
        return d

    @classmethod
    def get_attribute_dict_from_otl_assets(cls, drager: NodeInfoObject, toestellen: [NodeInfoObject],
                                           armatuur_controllers: [NodeInfoObject]) -> dict:
        toestel = toestellen[0]
        aantal_te_verlichten_rijvakken = toestel.attr_dict.get('VerlichtingstoestelLED.aantalTeVerlichtenRijstroken',
                                                               None)
        if aantal_te_verlichten_rijvakken is not None:
            aantal_te_verlichten_rijvakken = 'R' + aantal_te_verlichten_rijvakken[89:]

        datum_installatie_LED = toestel.attr_dict.get('AIMObject.datumOprichtingObject', None)

        kleurtemperatuur_LED = toestel.attr_dict.get('VerlichtingstoestelLED.kleurTemperatuur', None)
        if kleurtemperatuur_LED is not None:
            kleurtemperatuur_LED = 'K' + kleurtemperatuur_LED[70:]

        lichtpunthoogte = toestel.attr_dict.get('VerlichtingstoestelLED.lichtpuntHoogte')
        if lichtpunthoogte is not None:
            lichtpunthoogte = int(lichtpunthoogte[76:])

        lumen_pakket_LED = toestel.attr_dict.get('VerlichtingstoestelLED.lumenOutput')
        if lumen_pakket_LED is not None:
            lumen_pakket_LED = int(lumen_pakket_LED[67:])

        overhang_LED = toestel.attr_dict.get('VerlichtingstoestelLED.overhang')
        if overhang_LED is not None:
            overhang_LED = cls.map_overhang(overhang_LED)

        verlichtingsniveau = toestel.attr_dict.get('VerlichtingstoestelLED.verlichtingsNiveau')
        if verlichtingsniveau is not None:
            verlichtingsniveau = verlichtingsniveau[71:]

        merk = toestel.attr_dict.get('Verlichtingstoestel.merk')
        modelnaam = toestel.attr_dict.get('Verlichtingstoestel.modelnaam')
        merk_en_type = None
        if merk is not None and modelnaam is not None:
            merk = merk[79:]
            modelnaam = modelnaam[84:].title()
            merk_en_type = f'{merk} {modelnaam}'

        verlichtingstype = cls.get_verlichtingstype(toestellen)

        d = {
            'aantal_te_verlichten_rijvakken_LED': aantal_te_verlichten_rijvakken,
            'datum_installatie_LED': datum_installatie_LED,
            'kleurtemperatuur_LED': kleurtemperatuur_LED,
            'LED_verlichting': True,
            'lichtpunthoogte_tov_rijweg': lichtpunthoogte,
            'lumen_pakket_LED': lumen_pakket_LED,
            'overhang_LED': overhang_LED,
            'verlichtingsniveau_LED': verlichtingsniveau,
            'verlichtingstoestel_merk_en_type': merk_en_type,
            'verlichtingstoestel_systeemvermogen': toestel.attr_dict.get('Verlichtingstoestel.systeemvermogen'),
            'verlichtingstype': verlichtingstype,
            'aantal_verlichtingstoestellen': len(toestellen),

        }
        if drager.short_type == 'onderdeel#WVLichtmast':
            d['RAL_kleur'] = drager.attr_dict.get('Lichtmast.kleur')
            sorted_toestellen = sorted(toestellen, key=lambda t: t.attr_dict.get('AIMNaamObject.naam', ''))
            for index, toestel in enumerate(sorted_toestellen):
                toestel_naam = toestel.attr_dict.get('AIMNaamObject.naam')
                if toestel_naam is None:
                    continue
                ac = next((c for c in armatuur_controllers
                           if c.attr_dict.get('AIMNaamObject.naam', '').startswith(toestel_naam)), None)
                if ac is None:
                    continue
                d[f'serienummer_armatuurcontroller_{(index + 1)}'] = ac.attr_dict.get('Armatuurcontroller.serienummer',
                                                                                      None)

        return d

        d = {
            'contractnummer_levering_LED': drager.attr_dict.get('lgc:EMObject.contractnummerLeveringLed'), # via aanleveringsbestek
        }
        if drager.short_type == 'lgc:installatie#VPLMast':
            d['drager_buiten_gebruik'] = drager.attr_dict.get('lgc:VPLMast.lichtmastBuitenGebruik')
            d['serienummer_armatuurcontroller_1'] = drager.attr_dict.get('lgc:VPLMast.serienummerArmatuurcontroller1')
            d['serienummer_armatuurcontroller_2'] = drager.attr_dict.get('lgc:VPLMast.serienummerArmatuurcontroller2')
            d['serienummer_armatuurcontroller_3'] = drager.attr_dict.get('lgc:VPLMast.serienummerArmatuurcontroller3')
            d['serienummer_armatuurcontroller_4'] = drager.attr_dict.get('lgc:VPLMast.serienummerArmatuurcontroller4')



        return d

    @classmethod
    def get_update_dict(cls, drager_dict: dict, legacy_drager_dict: dict) -> dict:
        return {}

    @classmethod
    def map_overhang(cls, overhang_LED: str) -> str:
        return 'O+1'

    @classmethod
    def get_verlichtingstype(cls, toestellen: [NodeInfoObject]) -> str | None:
        map_dict = {
            'afrit': ('opafrit', 2),
            'bebakening': ('bebakening', 10),
            'doorlopende-straatverlichting': ('doorlopende straatverlichting', 11),
            'fietspad': ('fietspadverlichting', 12),
            'hoofdweg': ('hoofdbaan', 4),
            'kruispunt': ('kruispunt', 5),
            'monument': ('monument', 14),
            'onderdoorgang': ('onderdoorgang', 9),
            'oprit': ('opafrit', 2),
            'parking': ('parking', 13),
            'projector': ('projector', 100),
            'punctuele-verlichting': ('punctuele verlichting', 1),
            'rotonde': ('rotonde verlichting', 6),
            'tunnelverlichting': ('tunnel verlichting', 7),
            'wisselaar': ('wisselaar', 3),
            'onderdoorgang-dag': ('onderdoorgang dag', 8)
        }

        verlichtingstype_prio = 1000
        verlichtingstype = None
        for toestel in toestellen:
            verlichtingstype_node = toestel.attr_dict.get('Verlichtingstoestel.verlichtGebied')
            if verlichtingstype_node is not None:
                verlichtingstype_node = verlichtingstype_node[89:]
                verlichtingstype_tuple = map_dict[verlichtingstype_node]
                if verlichtingstype_tuple[1] < verlichtingstype_prio:
                    verlichtingstype_prio = verlichtingstype_tuple[1]
                    verlichtingstype = verlichtingstype_tuple[0]
        return verlichtingstype
