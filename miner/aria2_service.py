import json
import logging
import os
import sys
import time
import uuid
from datetime import date
from typing import List
from urllib.parse import urlparse

sys.path.append("../")
from common.config import read_config
from common.swan_client import SwanClient

from aria2c import Aria2c

config = read_config()
OUT_DIR = config['aria2']['aria2_download_dir']
api_url = config['main']['api_url']
api_key = config['main']['api_key']
access_token = config['main']['access_token']
miner_fid = config['main']['miner_fid']
client = SwanClient(api_url, api_key, access_token)

DEAL_DOWNLOADING_STATUS = 'Downloading'
DEAL_DOWNLOADED_STATUS = 'Downloaded'
DEAL_DOWNLOAD_FAILED_STATUS = 'DownloadFailed'
DEAL_CREATED_STATUS = 'Created'
DEAL_WAITING_STATUS = 'Waiting'

ARIA2_TASK_ACTIVE_STATUS = "active"
ARIA2_TASK_COMPLETE_STATUS = "complete"


def is_completed(_task):
    COMPLETE_STATUS = ARIA2_TASK_COMPLETE_STATUS

    failed = False
    success = True

    if _task['errorCode'] != '0':
        return failed

    if _task['totalLength'] == '0':
        return failed

    if _task["status"] == COMPLETE_STATUS and _task['completedLength'] == _task['totalLength']:
        return success
    return failed


def update_offline_deal_details(status: str, note: str, deal_id: str, file_path=None, file_size=None):
    try:
        client.update_offline_deal_details(status, note, deal_id, file_path, file_size)
    except Exception as e:
        logging.error("Failed to update offline deal status.")
        logging.error(str(e))


def find_next_deal_ready_to_download(miner_fid: str):
    try:
        deals = client.get_offline_deals(miner_fid, DEAL_CREATED_STATUS, str(1))
        if len(deals) == 0:
            deals = client.get_offline_deals(miner_fid, DEAL_WAITING_STATUS, str(1))
    except Exception as e:
        logging.error("Failed to find next ready to download deal.")
        logging.error(str(e))
        return None
    return deals


def find_deals_by_status(status: str, miner_fid: str):
    deals = []
    try:
        deals = client.get_offline_deals(miner_fid, status, str(50))
    except Exception as e:
        logging.error("Failed to find deals: " + status)
        logging.error(str(e))
    return deals


def start_download_for_deal(deal, client: Aria2c):
    logging.info("start downloading deal id %s" % str(deal.get("id")))
    file_resource_url = deal.get("file_source_url")
    filename = os.path.basename(urlparse(file_resource_url).path)
    today = date.today()
    option = {"out": filename,
              "dir": OUT_DIR + str(deal.get("user_id")) + '/' + today.strftime("%Y%m")}
    try:
        resp = json.loads(client.addUri(file_resource_url, option))
    except Exception as e:
        logging.error("Failed to download deal.")
        logging.error(str(e))
        update_offline_deal_details(DEAL_DOWNLOAD_FAILED_STATUS, deal["id"])

        return

    gid = resp['result']

    # todo extra rpc to get file path, change if find better method
    try:
        resp = client.getStatus(gid)
    except Exception as e:
        logging.error(e)
        note = "failed to start download %s" % e
        update_offline_deal_details(DEAL_DOWNLOAD_FAILED_STATUS, note, deal["id"])
        return

    files = resp['result']['files']
    if len(files) == 1:
        path = files[0]['path']
    else:
        logging.error("wrong file amount")
        return

    file_path = path
    update_offline_deal_details(DEAL_DOWNLOADING_STATUS, gid, deal["id"], file_path=file_path)


def check_download_status(client: Aria2c):
    try:
        note = ""
        file_size = 0
        downloading_deals = find_deals_by_status(DEAL_DOWNLOADING_STATUS, miner_fid)

        for deal in downloading_deals:
            current_status = deal.get("status")
            if deal.get("note"):
                note = deal.get("note")
                resp = client.getStatus(note)

                if resp:
                    task_state = resp['result']

                    # active downloading
                    if task_state["status"] == ARIA2_TASK_ACTIVE_STATUS:
                        complete_percent = int(
                            int(task_state["completedLength"]) / int(task_state["totalLength"]) * 10000) / 100
                        speed = int(int(task_state["downloadSpeed"]) / 1000)
                        logging.info("continue downloading deal cid %s complete %s%% speed %s KiB" % (
                            deal.get("cid"), complete_percent, speed))
                        continue

                    if is_completed(task_state):
                        # TODO: add md5 check
                        # if deal.is_md5_valid():
                        #     deal.status = DEAL_DOWNLOADED_STATUS
                        # else:
                        #     deal.status = DEAL_DOWNLOAD_FAILED_STATUS
                        #     deal.note = "md5 not match"
                        file_size = task_state["completedLength"]
                        new_status = DEAL_DOWNLOADED_STATUS
                    else:
                        new_status = DEAL_DOWNLOAD_FAILED_STATUS
                        note = "download failed, cause: %s" % task_state['errorMessage']
                else:
                    new_status = DEAL_DOWNLOAD_FAILED_STATUS
                    note = "download gid %s not found on aria2" % deal.get("note")

            else:
                new_status = DEAL_DOWNLOAD_FAILED_STATUS
                note = "download gid not found in offline_deals.note"

            if new_status != current_status:
                logging.info("deal id %s status %s -> %s" % (deal.get("id"), current_status, new_status))
                update_offline_deal_details(new_status, note, deal["id"], file_size=file_size)

    except Exception as e:
        logging.error("Failed to check download status.")
        logging.error(str(e))


def start_downloading(max_downloading_task_num: int, miner_fid, client: Aria2c):
    while True:
        try:
            downloading_deals = find_deals_by_status(DEAL_DOWNLOADING_STATUS, miner_fid)
            count_downloading_deals = len(downloading_deals)
            if max_downloading_task_num > count_downloading_deals:
                new_task_num = max_downloading_task_num - count_downloading_deals
                for i in range(new_task_num):
                    deal_to_download = find_next_deal_ready_to_download(miner_fid)
                    # no more deals
                    if deal_to_download is None or len(deal_to_download) == 0:
                        break
                    start_download_for_deal(deal_to_download[0], client)
                    time.sleep(1)
        finally:
            time.sleep(60)
