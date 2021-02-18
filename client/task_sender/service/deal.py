import csv
import logging.config
import math
import os
import re
import subprocess
import time
from decimal import Decimal

from common.OfflineDeal import OfflineDeal

logging.basicConfig(level=logging.DEBUG)

DURATION = '1051200'
EPOCH_PER_HOUR = 120


# 32GB
# PIECE_SIZE = '34091302912'

class DealConfig:
    miner_id = None
    sender_wallet = None
    max_price = None
    is_verified_deal = None
    epoch_interval_hours = None

    def __init__(self, miner_id, sender_wallet, max_price, is_verified_deal, epoch_interval_hours):
        self.miner_id = miner_id
        self.sender_wallet = sender_wallet
        self.max_price = max_price
        self.is_verified_deal = is_verified_deal
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
            logging.info('----- info: %s' % line)
            price_match = re.findall(r'''^Price per GiB: ([0-9]*\.?[0-9]+) FIL''', line)
            if len(price_match) != 0:
                price = price_match[0]

            verified_price_match = re.findall(r'''^Verified Price per GiB: ([0-9]*\.?[0-9]+) FIL''', line)
            if len(verified_price_match) != 0:
                verified_price = verified_price_match[0]
        return {'price': price,
                'verified_price': verified_price}


def propose_offline_deal(_price, piece_size, data_cid, piece_cid, deal_conf: DealConfig):
    start_epoch = get_current_epoch_by_current_time() + (deal_conf.epoch_interval_hours + 1) * EPOCH_PER_HOUR
    command = ['lotus', 'client', 'deal', '--from', deal_conf.sender_wallet, '--start-epoch', str(start_epoch),
               '--manual-piece-cid', piece_cid, '--manual-piece-size', piece_size, data_cid, deal_conf.miner_id, _price,
               DURATION]
    logging.info(command)
    input("Press Enter to continue...")
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    resp = proc.stdout.readline().rstrip().decode('utf-8')
    deal_cid = resp
    logging.info('deal cid: %s, start epoch: %s' % (deal_cid, start_epoch))
    return [deal_cid, start_epoch]


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
    return real_piece_size


def send_deals_to_miner(deal_conf: DealConfig, csv_file_path=None, deal_list=None):
    attributes = [i for i in OfflineDeal.__dict__.keys() if not i.startswith("__")]

    # todo init csv_file_path when deals are from deal_list
    output_csv_path = csv_file_path + ".output"
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
            if deal_conf.is_verified_deal:
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
            piece_size = str(calculate_piece_size_from_file_size(file_size))
        else:
            logging.error("file %s is too small" % _deal.source_file_name)
            continue

        # todo price here is price/Gb, need to calculate according to sector size
        result = propose_offline_deal(price, piece_size, data_cid, piece_cid, deal_conf)
        _deal_cid = result[0]
        _start_epoch = result[1]

        file_exists = os.path.isfile(output_csv_path)
        with open(output_csv_path, "a") as output_csv_file:
            output_fieldnames = ['miner_id', 'file_source_url', 'md5', 'start_epoch', 'deal_cid', 'timestamp']
            csv_writer = csv.DictWriter(output_csv_file, delimiter=',', fieldnames=output_fieldnames)
            if not file_exists:
                csv_writer.writeheader()
            csv_data = {
                'miner_id': deal_conf.miner_id,
                'file_source_url': source_file_url,
                'md5': md5,
                'start_epoch': _start_epoch,
                'deal_cid': _deal_cid,
                'timestamp': int(time.time() * 1000)
            }
            csv_writer.writerow(csv_data)
