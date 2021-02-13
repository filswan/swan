import json
import logging
import os

import requests

from common.Miner import Miner
from common.config import read_config


# task type
task_type_verified = "verified"
task_type_regular = "regular"

config = read_config()
api_url = config['main']['api_url']

class SwanTask:
    def __init__(self, task_name: str, is_public: bool, is_verified: bool):
        self.task_name = task_name
        self.is_public = is_public
        self.is_verified = is_verified

    def to_request_dict(self):
        return {
            'task_name': self.task_name,
            'is_public': 1 if self.is_public else 0,
            'type': task_type_verified if self.is_verified else task_type_regular
        }


class SwanClient:
    api_token = None

    def __init__(self, api_key, access_token):
        self.api_url = api_url
        self.api_key = api_key
        self.access_token = access_token
        self.refresh_token()

    def refresh_token(self):
        refresh_api_token_suffix = "/user/api_keys/jwt"
        refresh_api_token_method = 'POST'

        refresh_token_url = api_url + refresh_api_token_suffix
        data = {
            "apikey": self.api_key,
            "access_token": self.access_token
        }
        try:
            resp_data = send_http_request(refresh_token_url, refresh_api_token_method, None, json.dumps(data))
            self.api_token = resp_data['jwt']
        except Exception as e:
            logging.info(str(e))
            os._exit(1)

    def post_task(self, task: SwanTask, csv):
        create_task_url_suffix = '/tasks'
        create_task_method = 'POST'

        create_task_url = api_url + create_task_url_suffix
        payload_data = task.to_request_dict()

        send_http_request(create_task_url, create_task_method, self.api_token, payload_data, file=csv)

    def update_miner(self, miner: Miner):
        update_miner_url_suffix = '/miners/%s/status' % miner.miner_id
        update_miner_method = 'PUT'

        update_miner_url = api_url + update_miner_url_suffix
        payload_data = json.dumps(miner.to_request_dict())

        send_http_request(update_miner_url, update_miner_method, self.api_token, payload_data)

    def get_offline_deals(self, miner_fid: str):
        url = api_url + "/offline_deals/" + miner_fid + "?deal_status=ReadyForImport&limit=20&offset=0"
        get_offline_deals_method = "GET"
        try:
            response = send_http_request(url, get_offline_deals_method, self.api_token, None)
            return response["deal"]
        except Exception as e:
            return e

    def update_offline_deal_status(self, status: str, note: str, task_id: str, deal_cid: str):
        url = api_url + "/my_miner/tasks/" + task_id + "/deals/" + deal_cid
        update_offline_deal_status_method = "PUT"
        body = {"status": status, "note": note}
        send_http_request(url, update_offline_deal_status_method, self.api_token, body)


def send_http_request(url, method, token, payload, file=None):
    if isinstance(payload, str):
        headers = {'Content-Type': 'application/json'}
    elif isinstance(payload, dict):
        headers = {}
    else:
        headers = {}

    if token:
        headers["Authorization"] = "Bearer %s" % token

    payload_file = None
    if file:
        payload_file = {"file": file}

    with requests.request(url=url, method=method, headers=headers, data=payload, files=payload_file) as r:

        if r.status_code >= 400:
            raise Exception("response code %s " % r.status_code)
        else:
            json_body = r.json()
            if json_body['status'] != 'success' and json_body['status'] != 'Success':
                raise Exception("response status failed")
            else:
                return json_body['data']
