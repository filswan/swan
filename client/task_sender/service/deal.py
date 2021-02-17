import csv
import logging.config
import math
import os
import re
import subprocess
#   365 days
import time
from decimal import Decimal

from common.OfflineDeal import OfflineDeal

logging.config.fileConfig('logging.conf')

# create logger
logger = logging.getLogger(__name__)

MINERS = ['']
SENDER_WALLET = ""
MAX_PRICE = '0.000000018'
IS_VERIFIED_DEAL = True

DURATION = '1051200'
EPOCH_INTERVAL_HOURS = 96
EPOCH_PER_HOUR = 120


# 32GB
# PIECE_SIZE = '34091302912'


def get_current_epoch() -> int:
    current_epoch = None
    todo_epoch = None

    # 'lotus sycn wait'
    #   return immediately if node is synced
    #   wait for synchronization if node is not synced
    try:
        proc = subprocess.check_output(['lotus', 'sync', 'wait'], timeout=3)
        lines = proc.rstrip().decode('utf-8').split('\n')
    except subprocess.TimeoutExpired as e:
        print(e)
        lines = e.output.rstrip().decode('utf-8').split('\n')
    for line in lines:
        current_epoch_match = re.findall(r'''Target: (\d+)''', line)
        todo_epoch_match = re.findall(r'''Todo: (\d+)''', line)
        if len(current_epoch_match) > 0:
            current_epoch = int(current_epoch_match[0])
        if len(todo_epoch_match) > 0:
            todo_epoch = int(todo_epoch_match[0])

        if current_epoch and todo_epoch is not None:
            if todo_epoch < 5:
                break
            else:
                logger.error("node not synced")
                exit(1)
        else:
            continue

    # current_epoch might be 0 occasional
    if current_epoch == 0:
        logger.error("failed to get current epoch, value 0")
        exit(1)

    return current_epoch


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
        logger.error(e)
        logger.warning('lotus query-ask process not success.')
        return

    if proc is None:
        return
    else:
        lines = proc.rstrip().decode('utf-8').split('\n')

        for line in lines:
            logger.info('----- info: %s' % line)
            price_match = re.findall(r'''^Price per GiB: ([0-9]*\.?[0-9]+) FIL''', line)
            if len(price_match) != 0:
                price = price_match[0]

            verified_price_match = re.findall(r'''^Verified Price per GiB: ([0-9]*\.?[0-9]+) FIL''', line)
            if len(verified_price_match) != 0:
                verified_price = verified_price_match[0]
        return {'price': price,
                'verified_price': verified_price}


def propose_offline_deal(_miner, _price, piece_size, data_cid, piece_cid):
    start_epoch = get_current_epoch_by_current_time() + (EPOCH_INTERVAL_HOURS + 1) * EPOCH_PER_HOUR
    command = ['lotus', 'client', 'deal', '--from', SENDER_WALLET, '--start-epoch', str(start_epoch),
               '--manual-piece-cid', piece_cid, '--manual-piece-size', piece_size, data_cid, _miner, _price, DURATION]
    logger.info(command)
    input("Press Enter to continue...")
    # proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    # resp = proc.stdout.readline().rstrip().decode('utf-8')
    # deal_cid = resp
    deal_cid = 'deal_cid'
    logger.info('deal cid: %s, start epoch: %s' % (deal_cid, start_epoch))
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


def new(csv_file_path=None, deal_list=None):
    attributes = [i for i in OfflineDeal.__dict__.keys() if not i.startswith("__")]

    output_csv_path = csv_file_path + ".output"
    if deal_list:
        pass
    else:
        with open(csv_file_path, "r") as csv_file:
            fieldnames = attributes

        reader = csv.DictReader(csv_file, delimiter=',', fieldnames=fieldnames)
        next(reader, None)

    for _deal in deal_list:
        for miner in MINERS:
            data_cid = _deal.data_cid
            piece_cid = _deal.piece_cid
            source_file_url = _deal.source_file_url
            md5 = _deal.car_file_md5
            file_size = _deal.source_file_size
            prices = get_miner_price(miner)

            if prices:
                if IS_VERIFIED_DEAL:
                    price = prices['verified_price']
                else:
                    price = prices['price']
            else:
                continue

            if Decimal(price).compare(Decimal(MAX_PRICE)) > 0:
                logger.warning("miner %s price %s higher than max price %s" % (miner, price, MAX_PRICE))
                continue

            piece_size = str(calculate_piece_size_from_file_size(file_size))
            result = propose_offline_deal(miner, price, piece_size, data_cid, piece_cid)
            _deal_cid = result[0]
            _start_epoch = result[1]

            file_exists = os.path.isfile(output_csv_path)
            with open(output_csv_path, "a") as output_csv_file:
                output_fieldnames = ['miner_id', 'file_source_url', 'md5', 'start_epoch', 'deal_cid', 'timestamp']
                csv_writer = csv.DictWriter(output_csv_file, delimiter=',', fieldnames=output_fieldnames)
                if not file_exists:
                    csv_writer.writeheader()
                csv_data = {
                    'miner_id': miner,
                    'file_source_url': source_file_url,
                    'md5': md5,
                    'start_epoch': _start_epoch,
                    'deal_cid': _deal_cid,
                    'timestamp': int(time.time() * 1000)
                }
                csv_writer.writerow(csv_data)
