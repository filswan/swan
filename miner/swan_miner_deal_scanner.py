import logging.config
import sys
import os
import subprocess
import re
import time
import json
from datetime import datetime

sys.path.append("../")
from common.config import read_config
from common.swan_client import SwanClient

logging.config.fileConfig('./logging.conf')
logger = logging.getLogger(__name__)

DEAL_STATUS_FAILED = "ImportFailed"
DEAL_STATUS_WAITING = "ReadyForImport"
DEAL_STATUS_FILE_IMPORTING = "FileImporting"
DEAL_STATUS_FILE_IMPORTED = "FileImported"
DEAL_STATUS_ACTIVE = 'DealActive'
MESSAGE_TYPE_ON_CHAIN = "ON CHAIN"
MESSAGE_TYPE_SWAN = "SWAN"
ONCHAIN_DEAL_STATUS_ERROR = "StorageDealError"
ONCHAIN_DEAL_STATUS_ACTIVE = "StorageDealActive"
ONCHAIN_DEAL_STATUS_AWAITING = "StorageDealAwaitingPreCommit"

# Max number of deals to be scanned at a time
SCAN_NUMNBER = "100"

config = read_config()
api_url = config['main']['api_url']
api_key = config['main']['api_key']
access_token = config['main']['access_token']
client = SwanClient(api_url, api_key, access_token)

class OfflineDealMessage:

    def __init__(self, message_type, message_body, offline_deals_cid):
        self.message_type = message_type
        self.message_body = message_body
        self.offline_deals_cid = offline_deals_cid

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


def get_current_epoch():
    try:
        info_proving = subprocess.run(['lotus-miner', 'proving', 'info'], stdout=subprocess.PIPE).stdout.decode(
            'utf-8')
        current_epoch = int(re.search("(?<=Current Epoch: {11})[0-9]+", info_proving).group(0))
        return current_epoch
    except Exception as e:
        logger.error("Failed to get current epoch. Please check if miner is running properly.")
        logger.error(str(e))
        return -1


def update_offline_deal_status(status: str, note: str, deal_id: str):
    try:
        client.update_offline_deal_details(status, note, deal_id)
    except Exception as e:
        logger.error("Failed to update offline deal status.")
        logger.error(str(e))


def scanner():
    config = read_config()
    api_url = config['main']['api_url']
    api_key = config['main']['api_key']
    access_token = config['main']['access_token']
    scan_interval = config['main']['scan_interval']
    miner_fid = config['main']['miner_fid']

    while True:
        client = SwanClient(api_url, api_key, access_token)
        deals = client.get_offline_deals(miner_fid, DEAL_STATUS_FILE_IMPORTED, SCAN_NUMNBER)

        if deals is None or isinstance(deals, Exception):
            if isinstance(deals, Exception):
                logger.error(str(deals))
            logger.error("Failed to get offline deals.")
            logger.info("Sleeping...")
            time.sleep(scan_interval)
            continue

        if len(deals) == 0:
            logger.info("No ongoing offline deals found.")
            logger.info("Sleeping...")
            time.sleep(scan_interval)
            continue

        for deal in deals:
            deal_id = deal.get("id")
            deal_cid = deal.get("deal_cid")
            logger.info("ID: %s. Deal CID: %s. Deal Status: %s.", deal.get("id"), deal_cid, deal.get("status"))
            command = "lotus-miner storage-deals list -v | grep " + deal_cid
            try:
                pipe = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = pipe.communicate()
                if stderr != b'':
                    raise Exception(stderr)
                if stdout == b'':
                    note = "Failed to find deal on chain."
                    update_offline_deal_status(DEAL_STATUS_FAILED, note, deal_id)
                    raise Exception("Failed to find deal on chain. Deal ID: " + deal_id)
                stdout = stdout.decode("utf-8")
                logger.info("Deal details: %s", stdout)
                on_chain_message = ""
                # Deal status starts with StorageDeal, such as StorageDealError, StorageDealSealing etc.
                deal_status_index = stdout.find("StorageDeal", 0)
                on_chain_status = stdout[deal_status_index:stdout.find(' ', deal_status_index)]
                # Only ERROR deal has Message
                if on_chain_status == ONCHAIN_DEAL_STATUS_ERROR:
                    # Error message usually starts at bit 355
                    on_chain_message = stdout[355:].strip()
                    note = "Failed to find deal on chain."
                    update_offline_deal_status(DEAL_STATUS_FAILED, note, deal_id)
                    logger.info("Setting deal %s status as ImportFailed", deal_cid)
                if on_chain_status == ONCHAIN_DEAL_STATUS_ACTIVE:
                    deal_complete_note = "Deal has been completed"
                    update_offline_deal_status(DEAL_STATUS_ACTIVE, deal_complete_note, deal_id)
                    logger.info("Setting deal %s status as Active", deal_cid)
                if on_chain_status == ONCHAIN_DEAL_STATUS_AWAITING:
                    current_epoch = get_current_epoch()
                    if current_epoch != -1 and current_epoch > deal.get("start_epoch"):
                        note = "Sector is proved and active, while deal on chain status is " \
                               "StorageDealAwaitingPreCommit. Set deal status as ImportFailed."
                        update_offline_deal_status(DEAL_STATUS_FAILED, note, deal_id)
                        logger.info("Setting deal %s status as ImportFailed due to on chain status bug.", deal_cid)
                message = {
                    "on_chain_status": on_chain_status,
                    "on_chain_message": on_chain_message
                }
                offline_deal_message = OfflineDealMessage(message_type=MESSAGE_TYPE_ON_CHAIN,
                                                          message_body=json.dumps(message),
                                                          offline_deals_cid=deal_cid)
                # TODO: Update offline deal message to Swan
                logger.info("On chain offline_deal message created. Message Body: %s.", json.dumps(message))
                continue
            except Exception as e:
                message = {
                    "message": str(e)
                }
                offline_deal_message = OfflineDealMessage(message_type=MESSAGE_TYPE_SWAN,
                                                          message_body=json.dumps(message),
                                                          offline_deals_cid=deal_cid)
                # TODO: Update offline deal message to Swan
                logger.info("On chain offline_deal message created. Message Body: %s.", json.dumps(message))
                logger.error(str(e))
                continue
        logger.info("Sleeping...")
        time.sleep(scan_interval)
