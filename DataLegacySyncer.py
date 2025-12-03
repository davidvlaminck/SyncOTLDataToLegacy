import json
import logging
from itertools import batched
from pathlib import Path

from API.AbstractRequester import AbstractRequester
from API.DavieRestClient import DavieRestClient
from API.EMInfraRestClient import EMInfraRestClient
from API.EMsonImporter import EMsonImporter
from API.RequesterFactory import RequesterFactory
from Database.DbManager import DbManager
from Domain.AssetInfoCollector import AssetInfoCollector
from Domain.DeliveryFinder import DeliveryFinder
from Domain.Enums import AuthType, Environment
from Domain.ReportCreator import ReportCreator


class DataLegacySyncer:
    def __init__(self, settings_path: Path, auth_type: AuthType, env: Environment, state_db_path: Path):
        self.em_infra_client = EMInfraRestClient(self.create_requester_with_settings(
            settings_path=settings_path, auth_type=auth_type, env=env))
        self.emson_importer = EMsonImporter(self.create_requester_with_settings(
            settings_path=settings_path, auth_type=auth_type, env=env))
        self.davie_client = DavieRestClient(self.create_requester_with_settings(
            settings_path=settings_path, auth_type=auth_type, env=env))
        self.db_manager = DbManager(state_db_path=state_db_path)

    @classmethod
    def create_requester_with_settings(cls, settings_path: Path, auth_type: AuthType, env: Environment
                                       ) -> AbstractRequester:
        with open(settings_path) as settings_file:
            settings = json.load(settings_file)
        return RequesterFactory.create_requester(settings=settings, auth_type=auth_type, env=env)

    def run(self):
        self.find_deliveries_to_sync()

    def find_deliveries_to_sync(self):
        delivery_finder = DeliveryFinder(em_infra_client=self.em_infra_client, davie_client=self.davie_client,
                                         db_manager=self.db_manager)

        delivery_finder.find_deliveries_to_sync()

    def collect_and_create_multiple_specific_reports(self, report_information_tuples: list[tuple[str, str]],
                                                     only_use_delivery: bool = True):
        for report_information in report_information_tuples:
            asset_info_collector = AssetInfoCollector(em_infra_rest_client=self.em_infra_client,
                                                      emson_importer=self.emson_importer)
            asset_uuids = list(self.db_manager.get_asset_uuids_from_specific_deliveries(
                delivery_references=[report_information[1]]))
            self._collect_info_given_asset_uuids(asset_info_collector=asset_info_collector, asset_uuids=asset_uuids)
            self._create_all_reports(asset_info_collector=asset_info_collector,
                                     installatie_nummer=report_information[0],
                                     only_keep_specific_deliveries=only_use_delivery)
            self.print_collected_info_report(asset_info_collector=asset_info_collector)

    def collect_and_create_specific_reports(self, delivery_references: list[str], combine_single_report: bool = False,
                                            installatie_nummer: str = None):
        if combine_single_report:
            asset_info_collector = AssetInfoCollector(em_infra_rest_client=self.em_infra_client,
                                                      emson_importer=self.emson_importer)
            asset_uuids = list(self.db_manager.get_asset_uuids_from_specific_deliveries(
                delivery_references=delivery_references))
            self._collect_info_given_asset_uuids(asset_info_collector=asset_info_collector, asset_uuids=asset_uuids)
            self._create_all_reports(asset_info_collector=asset_info_collector, installatie_nummer=installatie_nummer)
            self.print_collected_info_report(asset_info_collector=asset_info_collector)
        else:
            for delivery_reference in delivery_references:
                asset_info_collector = AssetInfoCollector(em_infra_rest_client=self.em_infra_client,
                                                          emson_importer=self.emson_importer)
                asset_uuids = list(self.db_manager.get_asset_uuids_from_specific_deliveries(
                    delivery_references=[delivery_reference]))
                self._collect_info_given_asset_uuids(asset_info_collector=asset_info_collector, asset_uuids=asset_uuids)
                self._create_all_reports(asset_info_collector=asset_info_collector,
                                         installatie_nummer=installatie_nummer)
                self.print_collected_info_report(asset_info_collector=asset_info_collector)

    def collect_and_create_reports(self):
        asset_info_collector = AssetInfoCollector(em_infra_rest_client=self.em_infra_client,
                                                  emson_importer=self.emson_importer)
        asset_uuids = self.db_manager.get_asset_uuids_from_final_deliveries()
        self._collect_info_given_asset_uuids(asset_info_collector=asset_info_collector, asset_uuids=asset_uuids)
        self._create_all_reports(asset_info_collector=asset_info_collector)

    def poll_aanleveringen(self):
        pass
        # poll often to check for status 'Goedgekeurd'

    def update_legacy_data(self):
        pass
    # 4) update legacy data
    #     - [ ] find reports in state db that have sufficient information to using for updates
    #     - [ ] update legacy data using the state report until everything is marked as done
    #     - [ ] update the status of the aanlevering in state db to 'verwerkt'

    @classmethod
    def _collect_info_given_asset_uuids(cls,asset_info_collector: AssetInfoCollector, asset_uuids: list[str],
                                        batch_size: int = 10000):
        patterns = [
            (
                [("uuids", "of", "a"),
                 ("a", "type_of", ["VerlichtingstoestelLED"]),
                 ("a", "-[r1]-", "b"),
                 ("b", "type_of", ["onderdeel#WVLichtmast", "onderdeel#WVConsole"]),
                 ("r1", "type_of", ["onderdeel#Bevestiging"]),
                 ("a", "-[r1]-", "c"),
                 ("c", "type_of", ["onderdeel#Armatuurcontroller"]),
                 ("a", "-[r2]-", "d"),
                 ("d", "type_of", ["onderdeel#LEDDriver"]),
                 ("r2", "type_of", ["onderdeel#Bevestiging", "onderdeel#Sturing"]),
                 ("c", "-[r3]->", "d"),
                 ("r3", "type_of", ["onderdeel#VoedtAangestuurd"]),
                 ("e", "-[r3]->", "c"),
                 ("e", "type_of", ["onderdeel#Montagekast"]),
                 ("b", "-[r1]-", "e"),
                 ("b", "-[r4]->", "f"),
                 ("a", "-[r4]->", "f"),
                 ("f", "type_of", ["lgc:installatie#VPLMast", "lgc:installatie#VPConsole",
                                   "lgc:installatie#VPBevestig"]),
                 ("r4", "type_of", ["onderdeel#HoortBij"]),
                 ("c", "-[r5]-", "g"),
                 ("g", "type_of", ["onderdeel#Segmentcontroller"]),
                 ("r5", "type_of", ["onderdeel#Sturing"]),
                 ("g", "-[r4]-", "h"),
                 ("h", "type_of", ["lgc:installatie#SegC"])],
                "onderdeel#VerlichtingstoestelLED"
            ),
            (
                [("uuids", "of", "a"),
                 ("a", "type_of", ["onderdeel#Armatuurcontroller"]),
                 ("a", "-[r1]-", "b"),
                 ("b", "type_of", ["onderdeel#VerlichtingstoestelLED"]),
                 ("r1", "type_of", ["onderdeel#Bevestiging"]),
                 ("a", "-[r2]->", "c"),
                 ("c", "type_of", ["onderdeel#LEDDriver"]),
                 ("e", "-[r2]->", "a"),
                 ("e", "type_of", ["onderdeel#Montagekast"]),
                 ("r2", "type_of", ["onderdeel#VoedtAangestuurd"]),
                 ("a", "-[r3]-", "d"),
                 ("d", "type_of", ["onderdeel#Segmentcontroller"]),
                 ("r3", "type_of", ["onderdeel#Sturing"]),
                 ("b", "-[r4]-", "c"),
                 ("r4", "type_of", ["onderdeel#Bevestiging", "onderdeel#Sturing"]),
                 ("d", "-[r5]->", "f"),
                 ("f", "type_of", ["lgc:installatie#SegC"]),
                 ("r5", "type_of", ["onderdeel#HoortBij"]),
                 ("b", "-[r1]-", "g"),
                 ("e", "-[r1]-", "g"),
                 ("g", "type_of", ["onderdeel#WVLichtmast", "onderdeel#WVConsole"]),
                 ("b", "-[r5]->", "h"),
                 ("g", "-[r5]->", "h"),
                 ("h", "type_of", ["lgc:installatie#VPLMast", "lgc:installatie#VPConsole",
                                   "lgc:installatie#VPBevestig"])],
                "Armatuurcontroller"
            ),
            (
                [("uuids", "of", "a"),
                 ("a", "type_of", ["onderdeel#WVLichtmast", "onderdeel#WVConsole"]),
                 ("a", "-[r1]-", "b"),
                 ("a", "-[r1]-", "d"),
                 ("b", "type_of", ["onderdeel#VerlichtingstoestelLED"]),
                 ("d", "type_of", ["onderdeel#Montagekast"]),
                 ("a", "-[r2]->", "c"),
                 ("c", "type_of", ["lgc:installatie#VPLMast", "lgc:installatie#VPConsole"]),
                 ("r1", "type_of", ["onderdeel#Bevestiging"]),
                 ("r2", "type_of", ["onderdeel#HoortBij"]),
                 ("b", "-[r1]-", "e"),
                 ("b", "-[r1]-", "f"),
                 ("e", "type_of", ["onderdeel#LEDDriver"]),
                 ("f", "type_of", ["onderdeel#Armatuurcontroller"]),
                 ("d", "-[r3]->", "f"),
                 ("f", "-[r3]->", "e"),
                 ("r3", "type_of", ["onderdeel#VoedtAangestuurd"]),
                 ("f", "-[r4]-", "g"),
                 ("g", "type_of", ["onderdeel#Segmentcontroller"]),
                 ("r4", "type_of", ["onderdeel#Sturing"]),
                 ("g", "-[r2]->", "h"),
                 ("h", "type_of", ["lgc:installatie#SegC"])],
                "OTL drager"
            ),
            (
                [("uuids", "of", "a"),
                 ("a", "type_of", ["lgc:installatie#VPLMast", "lgc:installatie#VPConsole",
                                   "lgc:installatie#VPBevestig"]),
                 ("a", "<-[r1]-", "b"),
                 ("a", "<-[r1]-", "e"),
                 ("b", "type_of", ["onderdeel#WVLichtmast", "onderdeel#WVConsole"]),
                 ("e", "type_of", ["onderdeel#VerlichtingstoestelLED"]),
                 ("r1", "type_of", ["onderdeel#HoortBij"]),
                 ("c", "type_of", ["lgc:installatie#SegC"]),
                 ("c", "<-[r1]-", "d"),
                 ("d", "type_of", ["onderdeel#Segmentcontroller"]),
                 ("b", "-[r2]-", "e"),
                 ("b", "-[r2]-", "f"),
                 ("f", "type_of", ["onderdeel#Montagekast"]),
                 ("r2", "type_of", ["onderdeel#Bevestiging"]),
                 ("e", "-[r2]-", "g"),
                 ("e", "-[r2]-", "h"),
                 ("g", "type_of", ["onderdeel#LEDDriver"]),
                 ("h", "type_of", ["onderdeel#Armatuurcontroller"]),
                 ("f", "-[r3]->", "h"),
                 ("h", "-[r3]->", "g"),
                 ("r3", "type_of", ["onderdeel#VoedtAangestuurd"]),
                 ("h", "-[r4]-", "d"),
                 ("r4", "type_of", ["onderdeel#Sturing"])],
                "legacy assets"
            ),
        ]


        for pattern, description in patterns:
            cls._process_batches(pattern, description, asset_uuids, asset_info_collector,
                             batch_size=batch_size)
        # asset_uuids = keys from object_dict where the dict[key].is_relation is False
        asset_uuids = [k for k, v in asset_info_collector.collection.object_dict.items() if not v.is_relation]

        for pattern, description in patterns:
            cls._process_batches(pattern, description, asset_uuids, asset_info_collector,
                                 batch_size=batch_size)

    @classmethod
    def _process_batches(cls, pattern, description, asset_uuids, asset_info_collector, batch_size=1000):
        for uuids in batched(asset_uuids, batch_size):
            logging.info('collecting asset info')
            asset_info_collector.start_collecting_from_starting_uuids_using_pattern(
                starting_uuids=uuids,
                pattern=pattern)
            logging.info(f'collected asset info starting from {description}')

    def _create_all_reports(self, asset_info_collector, installatie_nummer: str = None,
                            only_keep_specific_deliveries: bool = False):
        report_creator = ReportCreator(collection=asset_info_collector.collection, db_manager=self.db_manager)
        report_creator.create_all_reports(installatie_nummer=installatie_nummer)

    def sync_specific_deliveries(self, context_strings: [str]):
        delivery_finder = DeliveryFinder(em_infra_client=self.em_infra_client, davie_client=self.davie_client,
                                         db_manager=self.db_manager)

        delivery_finder.sync_specific_deliveries(context_strings=context_strings)

    def process_report(self, report_path: Path = Path('Reports/report.xlsx'), installatie_nummer: str = None):
        report_creator = ReportCreator(collection=None, db_manager=self.db_manager)
        report_creator.process_report(report_path=report_path, em_infra_client=self.em_infra_client,
                                      installatie_nummer=installatie_nummer)

    def clear_specific_deliveries(self, context_strings: [str]):
        delivery_finder = DeliveryFinder(em_infra_client=self.em_infra_client, davie_client=self.davie_client,
                                         db_manager=self.db_manager)

        delivery_finder.clear_specific_deliveries(context_strings=context_strings)

    def print_collected_info_report(self, asset_info_collector: AssetInfoCollector):
        type_dict = {}
        for _, v in asset_info_collector.collection.object_dict.items():
            type_dict[v.short_type] = type_dict.get(v.short_type, 0) + 1

        logging.info('\033[92mCollected the following types and counts:\033[0m')
        for k, v in type_dict.items():
            logging.info(f'\033[92m{k}: {v}\033[0m')

