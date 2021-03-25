import csv
import logging.config
import math
import os
import re
import subprocess
import time
from decimal import Decimal
from pathlib import Path

from common.OfflineDeal import OfflineDeal

logging.basicConfig(level=logging.INFO)

DURATION = '1051200'
EPOCH_PER_HOUR = 120


# 32GB
# PIECE_SIZE = '34091302912'

class DealConfig:
    miner_id = None
    sender_wallet = None
    max_price = None
    verified_deal = None
    fast_retrieval = None
    epoch_interval_hours = None

    def __init__(self, miner_id, sender_wallet, max_price, verified_deal, fast_retrieval, epoch_interval_hours):
        self.miner_id = miner_id
        self.sender_wallet = sender_wallet
        self.max_price = max_price
        self.verified_deal = verified_deal
        self.fast_retrieval = fast_retrieval
        self.epoch_interval_hours = epoch_interval_hours


def get_current_epoch_by_current_time():
    current_timestamp = int(time.time())
    current_epoch = int((current_timestamp - 1598306471) / 30)
    return current_epoch


def get_miner_price(miner_fid: str):
    price = None
    verified_price = None

    try:
        proc = subprocess.check_output(['lotus', 'client', 'query-ask', miner_fid], timeout=60,
                                       stderr=subprocess.PIPE)

    except Exception as e:
        logging.error(e)
        logging.warning('lotus query-ask process not success.')
        return

    if proc is None:
        return
    else:
        lines = proc.rstrip().decode('utf-8').split('\n')

        for line in lines:
            price_match = re.findall(r'''^Price per GiB: ([0-9]*\.?[0-9]+) FIL''', line)
            if len(price_match) != 0:
                price = price_match[0]

            verified_price_match = re.findall(r'''^Verified Price per GiB: ([0-9]*\.?[0-9]+) FIL''', line)
            if len(verified_price_match) != 0:
                verified_price = verified_price_match[0]
        return {'price': price,
                'verified_price': verified_price}


def propose_offline_deal(_price, _cost, piece_size, data_cid, piece_cid, deal_conf: DealConfig, skip_confirmation: bool):
    start_epoch = get_current_epoch_by_current_time() + (deal_conf.epoch_interval_hours + 1) * EPOCH_PER_HOUR
    command = ['lotus', 'client', 'deal', '--from', deal_conf.sender_wallet, '--start-epoch', str(start_epoch),
               '--fast-retrieval=' + str(deal_conf.fast_retrieval).lower(), '--verified-deal=' + str(deal_conf.verified_deal).lower(),
               '--manual-piece-cid', piece_cid, '--manual-piece-size', piece_size, data_cid, deal_conf.miner_id, _cost,
               DURATION]
    logging.info(command)
    logging.info("wallet: %s" % deal_conf.sender_wallet)
    logging.info("miner: %s" % deal_conf.miner_id)
    logging.info("price: %s" % _price)
    logging.info("total cost: %s" % _cost)
    logging.info("start epoch: %s" % start_epoch)
    logging.info("fast-retrieval: %s" % str(deal_conf.fast_retrieval).lower())
    logging.info("verified-deal: %s" % str(deal_conf.verified_deal).lower())
    if not skip_confirmation:
        input("Press Enter to continue...")
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    resp = proc.stdout.readline().rstrip().decode('utf-8')
    deal_cid = resp
    logging.info('Deal sent, deal cid: %s, start epoch: %s' % (deal_cid, start_epoch))
    return deal_cid, start_epoch


# https://docs.filecoin.io/store/lotus/very-large-files/#maximizing-storage-per-sector
def calculate_piece_size_from_file_size(_file_size):
    _file_size = int(_file_size)
    exp = math.ceil(math.log(_file_size, 2))
    sector_size_to_to_check = 2 ** exp
    piece_size_to_check = int(sector_size_to_to_check * 254 / 256)
    if _file_size > piece_size_to_check:
        exp = exp + 1
    real_sector_size = 2 ** exp
    real_piece_size = int(real_sector_size * 254 / 256)
    return real_piece_size, real_sector_size


def calculate_real_cost(sector_size_bytes, price_per_GiB):
    bytes_per_GiB = 1024 * 1024 * 1024
    sector_size_in_GiB = Decimal(sector_size_bytes) / Decimal(bytes_per_GiB)

    real_cost = sector_size_in_GiB * Decimal(price_per_GiB)
    return real_cost


def send_deals_to_miner(deal_conf: DealConfig, output_dir, skip_confirmation: bool, task_name=None, csv_file_path=None, deal_list=None, task_uuid=None):

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    attributes = [i for i in OfflineDeal.__dict__.keys() if not i.startswith("__")]

    file_name_suffix = "-deals"

    if csv_file_path:
        csv_file_name = os.path.basename(csv_file_path)
        filename, file_ext = os.path.splitext(csv_file_name)
        output_csv_path = os.path.join(output_dir, filename + file_name_suffix + file_ext)
    else:
        output_csv_path = os.path.join(output_dir, task_name + file_name_suffix + ".csv")

    if deal_list:
        pass
    else:
        deal_list = []
        with open(csv_file_path, "r") as csv_file:
            fieldnames = attributes

            reader = csv.DictReader(csv_file, delimiter=',', fieldnames=fieldnames)
            next(reader, None)
            for row in reader:
                deal = OfflineDeal()
                for attr in row.keys():
                    deal.__setattr__(attr, row.get(attr))
                deal_list.append(deal)

    for _deal in deal_list:

        data_cid = _deal.data_cid
        piece_cid = _deal.piece_cid
        source_file_url = _deal.car_file_url
        md5 = _deal.car_file_md5
        file_size = _deal.source_file_size
        prices = get_miner_price(deal_conf.miner_id)

        if prices:
            if deal_conf.verified_deal:
                price = prices['verified_price']
            else:
                price = prices['price']
        else:
            continue

        if Decimal(price).compare(Decimal(deal_conf.max_price)) > 0:
            logging.warning(
                "miner %s price %s higher than max price %s" % (deal_conf.miner_id, price, deal_conf.max_price))
            continue
        if int(file_size) > 0:
            piece_size, sector_size = calculate_piece_size_from_file_size(file_size)
        else:
            logging.error("file %s is too small" % _deal.source_file_name)
            continue

        cost = f'{calculate_real_cost(sector_size, price):.18f}'

        _deal_cid, _start_epoch = propose_offline_deal(price, str(cost), str(piece_size), data_cid, piece_cid,
                                                       deal_conf, skip_confirmation)

        file_exists = os.path.isfile(output_csv_path)

        _deal.miner_id = deal_conf.miner_id
        _deal.start_epoch = _start_epoch
        _deal.deal_cid = _deal_cid

    logging.info("Swan deal final CSV Generated: %s" % output_csv_path)

    with open(output_csv_path, "w") as output_csv_file:
        output_fieldnames = ['uuid', 'miner_id', 'file_source_url', 'md5', 'start_epoch', 'deal_cid']
        csv_writer = csv.DictWriter(output_csv_file, delimiter=',', fieldnames=output_fieldnames)
        csv_writer.writeheader()

        for deal in deal_list:
            csv_data = {
                'uuid': task_uuid,
                'miner_id': deal_conf.miner_id,
                'file_source_url': deal.car_file_url,
                'md5': deal.car_file_md5,
                'start_epoch': deal.start_epoch,
                'deal_cid': deal.deal_cid
            }
            csv_writer.writerow(csv_data)

    return output_csv_path
