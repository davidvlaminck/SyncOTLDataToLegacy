import json
import logging
import math
import re

from pandas import DataFrame, concat

from Database.DbManager import DbManager
from Domain.AssetCollection import AssetCollection
from Domain.Enums import Direction
from Domain.InfoObject import NodeInfoObject


class ReportCreator:
    def __init__(self, collection: AssetCollection, db_manager: DbManager):
        self.collection = collection
        self.db_manager = db_manager

    def create_all_reports(self):
        df = self.start_creating_report_pov_legacy()
        df.to_excel('Reports/report_pov_legacy.xlsx')
        print('done writing report pov legacy')
        df = self.start_creating_report_pov_toestel()
        df.to_excel('Reports/report_pov_toestel.xlsx')
        print('done writing report pov toestel')
        df = self.start_creating_report_pov_armatuur_controller()
        df.to_excel('Reports/report_pov_ac.xlsx')
        print('done writing report pov ac')
        df = self.start_creating_report_pov_drager()
        df.to_excel('Reports/report_pov_drager.xlsx')
        print('done writing report pov drager')

    def start_creating_report_pov_drager(self) -> DataFrame:
        df = DataFrame()
        all_column_names = [
            'aanlevering_id', 'aanlevering_naam', 'drager_uuid', 'drager_naam', 'alles_ok',
            'drager_naam_conform_conventie', 'relatie_naar_toestel', 'relatie_naar_legacy_drager', 'kleur_ingevuld']

        for missing_column_name in all_column_names:
            df[missing_column_name] = None

        # get all dragers
        dragers = self.collection.get_node_objects_by_types(['onderdeel#WVLichtmast', 'onderdeel#WVConsole'])

        for drager in dragers:
            if not drager.active:
                continue
            deliveries = self.db_manager.get_deliveries_by_asset_uuid(asset_uuid=drager.uuid)
            if len(deliveries) == 0:
                aanlevering_naam = ''
                aanlevering_id = ''
            else:
                aanlevering_naam = '|'.join([d.referentie for d in deliveries])
                aanlevering_id = '|'.join([d.uuid_davie for d in deliveries if d.uuid_davie is not None])

            drager_uuid = drager.uuid
            drager_naam = drager.attr_dict.get('AIMNaamObject.naam', '')

            current_ac_drager_dict = {
                'aanlevering_id': [aanlevering_id], 'aanlevering_naam': [aanlevering_naam],
                'drager_uuid': [drager_uuid], 'drager_naam': [drager_naam],
            }

            record_dict = self.get_report_record_for_one_drager(drager=drager, record_dict=current_ac_drager_dict)
            df_current = DataFrame(record_dict)
            df = concat([df, df_current])

        return df.sort_values('drager_naam')

    def get_report_record_for_one_drager(self, drager: NodeInfoObject, record_dict: dict) -> dict:
        drager_uuid = drager.uuid
        drager_naam = drager.attr_dict.get('AIMNaamObject.naam', '')

        record_dict['drager_naam_conform_conventie'] = [self.is_conform_name_convention_drager_no_reference(
            drager_naam=drager_naam)]
        alles_ok = record_dict['drager_naam_conform_conventie'][0]

        toestellen = list(self.collection.traverse_graph(
            start_uuid=drager_uuid, relation_types=['Bevestiging'], allowed_directions=[Direction.NONE],
            return_type='info_object', filtered_node_types=['onderdeel#VerlichtingstoestelLED']))
        record_dict['relatie_naar_toestel'] = [(len(toestellen) > 0)]
        alles_ok = record_dict['relatie_naar_toestel'][0] and alles_ok

        legacy_dragers = list(self.collection.traverse_graph(
            start_uuid=drager_uuid, relation_types=['HoortBij'], allowed_directions=[Direction.WITH],
            return_type='info_object', filtered_node_types=['lgc:installatie#VPLMast', 'lgc:installatie#VPConsole']))
        record_dict['relatie_naar_legacy_drager'] = [(len(legacy_dragers) > 0)]
        alles_ok = record_dict['relatie_naar_legacy_drager'][0] and alles_ok

        if drager.short_type == 'onderdeel#WVLichtmast':
            record_dict['kleur_ingevuld'] = [(drager.attr_dict.get('Lichtmast.kleur', None) is not None)]
            alles_ok = record_dict['kleur_ingevuld'][0] and alles_ok

        record_dict['alles_ok'] = [alles_ok]
        return record_dict

    def start_creating_report_pov_armatuur_controller(self) -> DataFrame:
        df = DataFrame()
        all_column_names = [
            'aanlevering_id', 'aanlevering_naam', 'ac_uuid', 'ac_naam', 'alles_ok',
            'ac_naam_conform_conventie', 'relatie_naar_toestel', 'serienummer_ingevuld']

        for missing_column_name in all_column_names:
            df[missing_column_name] = None

        # get all armatuur controllers
        armatuur_controllers = self.collection.get_node_objects_by_types(['onderdeel#Armatuurcontroller'])

        for ac in armatuur_controllers:
            if not ac.active:
                continue
            deliveries = self.db_manager.get_deliveries_by_asset_uuid(asset_uuid=ac.uuid)
            if len(deliveries) == 0:
                aanlevering_naam = ''
                aanlevering_id = ''
            else:
                aanlevering_naam = '|'.join([d.referentie for d in deliveries])
                aanlevering_id = '|'.join([d.uuid_davie for d in deliveries if d.uuid_davie is not None])

            ac_uuid = ac.uuid
            ac_naam = ac.attr_dict.get('AIMNaamObject.naam', '')

            current_ac_drager_dict = {
                'aanlevering_id': [aanlevering_id], 'aanlevering_naam': [aanlevering_naam],
                'ac_uuid': [ac_uuid], 'ac_naam': [ac_naam],
            }

            record_dict = self.get_report_record_for_one_armatuur_controller(armatuur_controller=ac,
                                                                             record_dict=current_ac_drager_dict)
            df_current = DataFrame(record_dict)
            df = concat([df, df_current])

        return df.sort_values('ac_naam')

    def get_report_record_for_one_armatuur_controller(self, armatuur_controller: NodeInfoObject,
                                                      record_dict: dict) -> dict:
        ac_uuid = armatuur_controller.uuid
        ac_naam = armatuur_controller.attr_dict.get('AIMNaamObject.naam', '')

        record_dict['ac_naam_conform_conventie'] = [self.is_conform_name_convention_armatuur_controller_no_reference(
            ac_naam=ac_naam)]
        alles_ok = record_dict['ac_naam_conform_conventie'][0]

        toestellen = list(self.collection.traverse_graph(
            start_uuid=ac_uuid, relation_types=['Bevestiging'], allowed_directions=[Direction.NONE],
            return_type='info_object', filtered_node_types=['onderdeel#VerlichtingstoestelLED']))
        record_dict['relatie_naar_toestel'] = [(len(toestellen) > 0)]
        alles_ok = record_dict['relatie_naar_toestel'][0] and alles_ok

        record_dict['serienummer_ingevuld'] = [
            (armatuur_controller.attr_dict.get('Armatuurcontroller.serienummer', None) is not None)]
        alles_ok = record_dict['serienummer_ingevuld'][0] and alles_ok

        record_dict['alles_ok'] = [alles_ok]
        return record_dict

    def start_creating_report_pov_toestel(self) -> DataFrame:
        df = DataFrame()
        all_column_names = [
            'aanlevering_id', 'aanlevering_naam', 'toestel_uuid', 'toestel_naam', 'alles_ok',
            'toestel_naam_conform_conventie',
            'relatie_naar_armatuur_controller', 'relatie_naar_otl_of_legacy_drager',
            'aantalTeVerlichtenRijstroken_ingevuld', 'datumOprichtingObject_ingevuld', 'kleurTemperatuur_ingevuld',
            'lichtpuntHoogte_ingevuld', 'lumenOutput_ingevuld', 'overhang_ingevuld', 'verlichtingsNiveau_ingevuld',
            'merk_ingevuld', 'modelnaam_ingevuld', 'verlichtGebied_ingevuld', 'systeemvermogen_ingevuld']

        for missing_column_name in all_column_names:
            df[missing_column_name] = None

        # get all toestellen
        toestellen = self.collection.get_node_objects_by_types(['onderdeel#VerlichtingstoestelLED'])

        for toestel in toestellen:
            if not toestel.active:
                continue
            deliveries = self.db_manager.get_deliveries_by_asset_uuid(asset_uuid=toestel.uuid)
            if len(deliveries) == 0:
                aanlevering_naam = ''
                aanlevering_id = ''
            else:
                aanlevering_naam = '|'.join([d.referentie for d in deliveries])
                aanlevering_id = '|'.join([d.uuid_davie for d in deliveries if d.uuid_davie is not None])

            toestel_uuid = toestel.uuid
            toestel_naam = toestel.attr_dict.get('AIMNaamObject.naam', '')

            current_toestel_drager_dict = {
                'aanlevering_id': [aanlevering_id], 'aanlevering_naam': [aanlevering_naam],
                'toestel_uuid': [toestel_uuid], 'toestel_naam': [toestel_naam],
            }

            record_dict = self.get_report_record_for_one_toestel(toestel=toestel,
                                                                 record_dict=current_toestel_drager_dict)
            df_current = DataFrame(record_dict)
            df = concat([df, df_current])

        return df.sort_values('toestel_naam')

    def get_report_record_for_one_toestel(self, toestel: NodeInfoObject, record_dict: dict) -> dict:
        toestel_uuid = toestel.uuid
        toestel_naam = toestel.attr_dict.get('AIMNaamObject.naam', '')

        record_dict['toestel_naam_conform_conventie'] = [self.is_conform_name_convention_toestel_no_reference(
            toestel_naam=toestel_naam)]
        alles_ok = record_dict['toestel_naam_conform_conventie'][0]

        armatuur_controllers = list(self.collection.traverse_graph(
            start_uuid=toestel_uuid, relation_types=['Bevestiging'], allowed_directions=[Direction.NONE],
            return_type='info_object', filtered_node_types=['onderdeel#Armatuurcontroller']))
        record_dict['relatie_naar_armatuur_controller'] = [(len(armatuur_controllers) > 0)]
        alles_ok = record_dict['relatie_naar_armatuur_controller'][0] and alles_ok

        dragers = list(self.collection.traverse_graph(
            start_uuid=toestel_uuid, relation_types=['HoortBij', 'Bevestiging'],
            allowed_directions=[Direction.REVERSED, Direction.NONE], return_type='info_object',
            filtered_node_types=['onderdeel#WVLichtmast', 'onderdeel#WVConsole', 'lgc:installatie#VPBevestig']))
        record_dict['relatie_naar_otl_of_legacy_drager'] = [(len(dragers) > 0)]
        alles_ok = record_dict['relatie_naar_otl_of_legacy_drager'][0] and alles_ok

        record_dict['aantalTeVerlichtenRijstroken_ingevuld'] = [
            (toestel.attr_dict.get('VerlichtingstoestelLED.aantalTeVerlichtenRijstroken', None) is not None)]
        alles_ok = record_dict['aantalTeVerlichtenRijstroken_ingevuld'][0] and alles_ok

        record_dict['datumOprichtingObject_ingevuld'] = [
            (toestel.attr_dict.get('AIMObject.datumOprichtingObject', None) is not None)]
        alles_ok = record_dict['datumOprichtingObject_ingevuld'][0] and alles_ok

        record_dict['kleurTemperatuur_ingevuld'] = [
            (toestel.attr_dict.get('VerlichtingstoestelLED.kleurTemperatuur', None) is not None)]
        alles_ok = record_dict['kleurTemperatuur_ingevuld'][0] and alles_ok

        record_dict['lichtpuntHoogte_ingevuld'] = [
            (toestel.attr_dict.get('VerlichtingstoestelLED.lichtpuntHoogte', None) is not None)]
        alles_ok = record_dict['lichtpuntHoogte_ingevuld'][0] and alles_ok

        record_dict['lumenOutput_ingevuld'] = [
            (toestel.attr_dict.get('VerlichtingstoestelLED.lumenOutput', None) is not None)]
        alles_ok = record_dict['lumenOutput_ingevuld'][0] and alles_ok

        record_dict['overhang_ingevuld'] = [
            (toestel.attr_dict.get('VerlichtingstoestelLED.overhang', None) is not None)]
        alles_ok = record_dict['overhang_ingevuld'][0] and alles_ok

        record_dict['verlichtingsNiveau_ingevuld'] = [
            (toestel.attr_dict.get('VerlichtingstoestelLED.verlichtingsNiveau', None) is not None)]
        alles_ok = record_dict['verlichtingsNiveau_ingevuld'][0] and alles_ok

        record_dict['merk_ingevuld'] = [
            (toestel.attr_dict.get('Verlichtingstoestel.merk', None) is not None)]
        alles_ok = record_dict['merk_ingevuld'][0] and alles_ok

        record_dict['modelnaam_ingevuld'] = [
            (toestel.attr_dict.get('Verlichtingstoestel.modelnaam', None) is not None)]
        alles_ok = record_dict['modelnaam_ingevuld'][0] and alles_ok

        record_dict['verlichtGebied_ingevuld'] = [
            (toestel.attr_dict.get('Verlichtingstoestel.verlichtGebied', None) is not None)]
        alles_ok = record_dict['verlichtGebied_ingevuld'][0] and alles_ok

        record_dict['systeemvermogen_ingevuld'] = [
            (toestel.attr_dict.get('Verlichtingstoestel.systeemvermogen', None) is not None)]
        alles_ok = record_dict['systeemvermogen_ingevuld'][0] and alles_ok

        record_dict['alles_ok'] = [alles_ok]
        return record_dict

    def start_creating_report_pov_legacy(self) -> DataFrame:
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
            if not drager.active:
                continue
            deliveries = self.db_manager.get_deliveries_by_asset_uuid(asset_uuid=drager.uuid)
            if len(deliveries) == 0:
                aanlevering_naam = ''
                aanlevering_id = ''
            else:
                aanlevering_naam = '|'.join([d.referentie for d in deliveries])
                aanlevering_id = '|'.join([d.uuid_davie for d in deliveries if d.uuid_davie is not None])
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

        return df.sort_values('legacy_drager_naampad')

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
            record_dict['update_legacy_drager_geometrie'] = ''

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
        toestel = cls.get_toestel_by_index(toestellen=toestellen, index=1)
        if toestel is None:
            return {'error': 'toestel 1 kon niet worden gevonden'}

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
            lichtpunthoogte = lichtpunthoogte[76:].replace('-', '.')
            try:
                lichtpunthoogte = float(lichtpunthoogte)
            except:
                logging.error(f'could not convert {lichtpunthoogte}')

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
            for index in range(1, len(toestellen) + 1):
                ac = cls.get_armatuur_controller_by_index(armatuur_controllers=armatuur_controllers, index=index)
                if ac is None:
                    continue
                d[f'serienummer_armatuurcontroller_{index}'] = ac.attr_dict.get('Armatuurcontroller.serienummer', None)
        return d

        # TODO
        d = {
            'contractnummer_levering_LED': drager.attr_dict.get('lgc:EMObject.contractnummerLeveringLed'),
            # via aanleveringsbestek
        }
        if drager.short_type == 'lgc:installatie#VPLMast':
            d['drager_buiten_gebruik'] = drager.attr_dict.get('lgc:VPLMast.lichtmastBuitenGebruik')

        return d

    @classmethod
    def get_update_dict(cls, drager_dict: dict, legacy_drager_dict: dict) -> dict:
        # TODO compare legacy with otl drager and create a dict that's the difference of those two
        update_dict = {}
        for key, value in drager_dict.items():
            if key not in legacy_drager_dict:
                update_dict[key] = value
            elif value != legacy_drager_dict[key]:
                update_dict[key] = value
        return update_dict

    @classmethod
    def map_overhang(cls, overhang_LED: str) -> str | None:
        map_dict = {
            '0-2': '0',
            '0-5': '+0.5',
            '0-5-2': '-0.5',
            '1-0': '+1.0',
            '1-0-2': '-1.0',
            '1-5': '+1.5',
            '1-5-2': '-1.5',
            '2-0': '+2.0',
            '2-0-2': '-2.0',
            '2-5': '+2.5',
            '2-5-2': '-2.5',
            '3-0': '+3.0',
            '3-0-2': '-3.0',
            '3-5': '+3.5',
            '3-5-2': '-3.5',
            '4': '-4',
            '4-2': '+4',
            '4-5': '+4.5',
            '4-5-2': '-4.5',
            '5-0': '+5.0',
            '5-0-2': '-5.0',
            '5-5': '+5.5',
            '5-5-2': '-5.5',
            '6-0': '+6.0',
            '6-0-2': '-6.0',
            '6-5': '+6.5',
            '6-5-2': '-6.5',
            '7-0': '+7.0',
            '7-0-2': '-7.0'}
        overhang = map_dict.get(overhang_LED[69:])
        if overhang is None:
            return None
        if overhang == '0':
            return '0'
        if overhang.endswith('.0'):
            overhang = overhang[:-2]

        return f'O{overhang}'

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

    @classmethod
    def get_armatuur_controller_by_index(cls, armatuur_controllers: [NodeInfoObject], index: int
                                         ) -> NodeInfoObject | None:
        index_str = str(index)
        for ac in armatuur_controllers:
            naam = ac.attr_dict.get('AIMNaamObject.naam')
            if naam and naam.split('.')[-2][2:3] == index_str:
                return ac

    @classmethod
    def get_toestel_by_index(cls, toestellen: [NodeInfoObject], index: int) -> NodeInfoObject | None:
        index_str = str(index)
        for toestel in toestellen:
            naam = toestel.attr_dict.get('AIMNaamObject.naam')
            if naam and naam[-1] == index_str:
                return toestel

    def is_conform_name_convention_toestel_no_reference(self, toestel_naam: str) -> bool:
        if '.' not in toestel_naam:
            return False
        parts = toestel_naam.split('.')
        if len(parts) != 3:
            return False
        if not re.match('^(A|C|G|WO|WW)[0-9]{4}$', parts[0]):
            return False
        if parts[2][0:2] != 'WV':
            return False
        return True

    def is_conform_name_convention_armatuur_controller_no_reference(self, ac_naam: str) -> bool:
        if '.' not in ac_naam:
            return False
        parts = ac_naam.split('.')
        if len(parts) != 4:
            return False
        if not re.match('^(A|C|G|WO|WW)[0-9]{4}$', parts[0]):
            return False
        if parts[2][0:2] != 'WV':
            return False
        if parts[3][0:2] != 'AC':
            return False
        return True

    def is_conform_name_convention_drager_no_reference(self, drager_naam: str) -> bool:
        if '.' not in drager_naam:
            return False
        parts = drager_naam.split('.')
        if len(parts) != 2:
            return False
        if not re.match('^(A|C|G|WO|WW)[0-9]{4}$', parts[0]):
            return False
        return True
