import logging.config
import re
import subprocess
import sys
import time

sys.path.append("../")
from common.config import read_config
from common.swan_client import SwanClient

DEAL_STATUS_FAILED = "ImportFailed"
DEAL_STATUS_READY = "ReadyForImport"
DEAL_STATUS_FILE_IMPORTING = "FileImporting"
DEAL_STATUS_FILE_IMPORTED = "FileImported"
DEAL_STATUS_ACTIVE = 'DealActive'

ONCHAIN_DEAL_STATUS_ERROR = "StorageDealError"
ONCHAIN_DEAL_STATUS_ACTIVE = "StorageDealActive"
ONCHAIN_DEAL_STATUS_NOTFOUND = "StorageDealNotFound"
ONCHAIN_DEAL_STATUS_WAITTING = "StorageDealWaitingForData"
ONCHAIN_DEAL_STATUS_ACCEPT = "StorageDealAcceptWait"

# Max number of deals to be imported at a time
IMPORT_NUMNBER = "20"

config = read_config()
api_url = config['main']['api_url']
api_key = config['main']['api_key']
access_token = config['main']['access_token']
client = SwanClient(api_url, api_key, access_token)


def get_deal_on_chain_status(deal_cid: str):
    cmd = "lotus-miner storage-deals list -v | grep " + deal_cid

    try:
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = pipe.communicate()

        if stderr != b'':
            return stderr.decode("utf-8")
        if stdout == b'':
            return ONCHAIN_DEAL_STATUS_NOTFOUND

        stdout = stdout.decode("utf-8")
        # Deal status starts with StorageDeal, such as StorageDealError, StorageDealSealing etc.
        deal_status_index = stdout.find("StorageDeal", 0)
        return stdout[deal_status_index:stdout.find(' ', deal_status_index)]

    except Exception as error:
        return str(error)


def update_offline_deal_status(status: str, note: str, deal_id: str):
    logger = logging.getLogger('swan_miner_deal_importer')
    try:
        client.update_offline_deal_details(status, note, deal_id)
    except Exception as e:
        logger.error("Failed to update offline deal status.")
        logger.error(str(e))


def importer():
    logger = logging.getLogger('swan_miner_deal_importer')
    config = read_config()
    api_url = config['main']['api_url']
    api_key = config['main']['api_key']
    access_token = config['main']['access_token']
    import_interval = config['main']['import_interval']
    expected_sealing_time = config['main']['expected_sealing_time']
    miner_fid = config['main']['miner_fid']

    while True:
        client = SwanClient(api_url, api_key, access_token)
        deals = client.get_offline_deals(miner_fid, DEAL_STATUS_READY, IMPORT_NUMNBER)

        if deals is None or isinstance(deals, Exception):
            if isinstance(deals, Exception):
                logger.error(str(deals))
            logger.error("Failed to get offline deals.")
            logger.info("Sleeping...")
            time.sleep(import_interval)
            continue

        if len(deals) == 0:
            logger.info("No pending offline deals found.")
            logger.info("Sleeping...")
            time.sleep(import_interval)
            continue

        for deal in deals:
            logger.info('')
            logger.info("Deal CID: %s. File Path: %s", deal["deal_cid"], deal["file_path"], )

            on_chain_status = get_deal_on_chain_status(deal["deal_cid"])
            if on_chain_status.startswith("StorageDeal") is False:
                logger.error(on_chain_status)
                logger.error("Failed to get deal on chain status, please check if lotus-miner is running properly.")
                logger.info("Sleeping...")
                time.sleep(import_interval)
                break

            logger.info("Deal on chain status: %s.", on_chain_status)

            if on_chain_status == ONCHAIN_DEAL_STATUS_ERROR:
                logger.info("Deal on chain status is error before importing.")
                note = "Deal error before importing."
                update_offline_deal_status(DEAL_STATUS_FAILED, note, str(deal["id"]))
                continue

            if on_chain_status == ONCHAIN_DEAL_STATUS_ACTIVE:
                logger.info("Deal on chain status is active before importing.")
                note = "Deal active before importing."
                update_offline_deal_status(DEAL_STATUS_ACTIVE, note, str(deal["id"]))
                continue

            if on_chain_status == ONCHAIN_DEAL_STATUS_ACCEPT:
                logger.info("Deal on chain status is StorageDealAcceptWait. Deal will be ready shortly.")
                continue

            if on_chain_status == ONCHAIN_DEAL_STATUS_NOTFOUND:
                logger.info("Deal on chain status not found.")
                note = "Deal not found."
                update_offline_deal_status(DEAL_STATUS_FAILED, note, str(deal["id"]))
                continue

            if on_chain_status != ONCHAIN_DEAL_STATUS_WAITTING:
                logger.info("Deal is already imported, please check.")
                note = on_chain_status
                update_offline_deal_status(DEAL_STATUS_FILE_IMPORTED, note, str(deal["id"]))
                continue

            try:
                info_proving = subprocess.run(['lotus-miner', 'proving', 'info'], stdout=subprocess.PIPE).stdout.decode(
                    'utf-8')
                current_epoch = int(re.search("(?<=Current Epoch: {11})[0-9]+", info_proving).group(0))
            except Exception as e:
                logger.error("Failed to get current epoch. Please check if miner is running properly.")
                logger.error(str(e))
                logger.info("Sleeping...")
                time.sleep(import_interval)
                break

            logger.info("Current epoch: %s. Deal starting epoch: %s", current_epoch, deal.get("start_epoch"))
            try:
                if deal.get("start_epoch") - current_epoch < expected_sealing_time:
                    logger.info("Deal will start too soon. Do not import this deal.")
                    note = "Deal expired."
                    update_offline_deal_status(DEAL_STATUS_FAILED, note, str(deal["id"]))
                    continue

                command = "lotus-miner storage-deals import-data " + deal.get("deal_cid") + " " + deal.get("file_path")
                logger.info('Command: %s' % command)

                note = ""
                update_offline_deal_status(DEAL_STATUS_FILE_IMPORTING, note, str(deal["id"]))

                pipe = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out, err = pipe.communicate()

                # There should be no output if everything goes well
                if out != b'':
                    update_offline_deal_status(DEAL_STATUS_FAILED, str(out), str(deal["id"]))
                    logger.error("Import deal failed. CID: %s. Error message: %s", deal["deal_cid"], str(out))
                    continue

                update_offline_deal_status(DEAL_STATUS_FILE_IMPORTED, "", str(deal["id"]))

                logger.info("Deal CID %s imported.", deal["deal_cid"])
                logger.info("Sleeping...")
                time.sleep(import_interval)

            except Exception as e:
                logger.error("Import deal failed. CID: %s. Error message: %s", deal["deal_cid"], str(e))
                note = str(e)
                update_offline_deal_status(DEAL_STATUS_FAILED, note, str(deal["id"]))
                continue

        logger.info("Sleeping...")
        time.sleep(import_interval)
