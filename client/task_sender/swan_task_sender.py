import csv
import logging
import os
import time
from os import listdir
from os.path import isfile, join
from pathlib import Path
from typing import List

from common.OfflineDeal import OfflineDeal
from common.config import read_config
from common.swan_client import SwanClient, SwanTask
from .deal_sender import send_deals
from .service.file_process import checksum, stage_one


def read_file_path_in_dir(dir_path: str) -> List[str]:
    _file_paths = [join(dir_path, f) for f in listdir(dir_path) if isfile(join(dir_path, f))]
    return _file_paths


def generate_csv_and_send(_task: SwanTask, deal_list: List[OfflineDeal], _output_dir: str, _client: SwanClient):
    _csv_name = _task.task_name + ".csv"
    _csv_path = os.path.join(_output_dir, _csv_name)

    logging.info('Swan task CSV %s' % _csv_path)
    with open(_csv_path, "a") as csv_file:
        fieldnames = ['miner_id', 'deal_cid', 'file_source_url', 'md5', 'start_epoch']
        csv_writer = csv.DictWriter(csv_file, delimiter=',', fieldnames=fieldnames)
        csv_writer.writeheader()
        for _deal in deal_list:
            csv_data = {
                'miner_id': _deal.miner_id,
                'deal_cid': _deal.deal_cid,
                'file_source_url': _deal.car_file_url,
                'md5': _deal.car_file_md5 if _deal.car_file_md5 else "",
                'start_epoch': _deal.start_epoch
            }
            csv_writer.writerow(csv_data)

    if _client:
        with open(_csv_path, "r") as csv_file:
            _client.post_task(_task, csv_file)


def generate_car(_deal_list: List[OfflineDeal], target_dir) -> List[OfflineDeal]:
    for _deal in _deal_list:
        car_file_name = _deal.source_file_name + ".car"
        car_file_path = os.path.join(target_dir, car_file_name)
        if os.path.isfile(car_file_path):
            car_file_name = _deal.source_file_name + str(int(time.time())) + ".car"
            car_file_path = os.path.join(target_dir, car_file_name)

        _deal.car_file_name = car_file_name
        _deal.car_file_path = car_file_path

        if _deal.car_file_md5:
            car_md5 = checksum(car_file_path)
            _deal.car_file_md5 = car_md5

        piece_cid, data_cid = stage_one(_deal.source_file_path, car_file_path)
        _deal.piece_cid = piece_cid
        _deal.data_cid = data_cid
        _deal.car_file_size = os.path.getsize(car_file_path)

    return _deal_list


def generate_metadata_csv(_deal_list: List[OfflineDeal], _task: SwanTask, _out_dir: str):
    attributes = [i for i in OfflineDeal.__dict__.keys() if not i.startswith("__")]
    _csv_path = os.path.join(_out_dir, "%s-metadata.csv" % _task.task_name)

    logging.info('Metadata CSV %s' % _csv_path)
    with open(_csv_path, "a") as csv_file:
        fieldnames = attributes
        csv_writer = csv.DictWriter(csv_file, delimiter=',', fieldnames=fieldnames)
        csv_writer.writeheader()
        for _deal in _deal_list:
            csv_writer.writerow(_deal.__dict__)


def create_new_task(input_dir, config_path, task_name, miner_id=None):
    # todo move config reading to cli level
    config = read_config(config_path)
    output_dir = config['sender']['output_dir']
    is_public = config['sender']['is_public']
    is_verified = config['sender']['is_verified']
    generate_md5 = config['sender']['generate_md5']
    offline_mode = config['sender']['offline_mode']

    api_url = config['main']['api_url']
    api_key = config['main']['api_key']
    access_token = config['main']['access_token']

    host = config['web-server']['host']
    port = config['web-server']['port']
    path = config['web-server']['path']

    download_url_prefix = str(host).rstrip("/")
    download_url_prefix = download_url_prefix + ":" + str(port)

    path = str(path).strip("/")
    if path:
        download_url_prefix = os.path.join(download_url_prefix, path)

    if not is_public:
        if not miner_id:
            print('Please provide --miner')
            exit(1)

    file_paths = read_file_path_in_dir(input_dir)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    deal_list: List[OfflineDeal] = []

    for file_path in file_paths:
        source_file_name = os.path.basename(file_path)

        offline_deal = OfflineDeal()
        offline_deal.source_file_name = source_file_name
        offline_deal.source_file_path = file_path
        offline_deal.source_file_size = os.path.getsize(file_path)
        if generate_md5:
            offline_deal.car_file_md5 = True
        deal_list.append(offline_deal)

    generate_car(deal_list, output_dir)

    for deal in deal_list:
        deal.car_file_url = os.path.join(download_url_prefix, deal.car_file_name)

    if not is_public:
        send_deals(config_path, miner_id, task_name, deal_list=deal_list)

    if offline_mode:
        client = None
    else:
        client = SwanClient(api_url, api_key, access_token)

    task = SwanTask(
        task_name=task_name,
        is_public=is_public,
        is_verified=is_verified
    )

    if miner_id:
        task.miner_id = miner_id
    generate_metadata_csv(deal_list, task, output_dir)
    generate_csv_and_send(task, deal_list, output_dir, client)
