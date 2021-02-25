import json
import logging

import requests

from common.Miner import Miner

# task type
task_type_verified = "verified"
task_type_regular = "regular"


class SwanTask:
    miner_id = None

    def __init__(self, task_name: str, is_public: bool, is_verified: bool):
        self.task_name = task_name
        self.is_public = is_public
        self.is_verified = is_verified

    def to_request_dict(self):
        return {
            'task_name': self.task_name,
            'is_public': 1 if self.is_public else 0,
            'type': task_type_verified if self.is_verified else task_type_regular,
            'miner_id': self.miner_id if self.miner_id else ''
        }


class SwanClient:
    api_token = None

    def __init__(self, api_url, api_key, access_token):
        self.api_url = api_url
        self.api_key = api_key
        self.access_token = access_token
        self.refresh_token()

    def refresh_token(self):
        logging.info('Refreshing token')
        refresh_api_token_suffix = "/user/api_keys/jwt"
        refresh_api_token_method = 'POST'

        refresh_token_url = self.api_url + refresh_api_token_suffix
        data = {
            "apikey": self.api_key,
            "access_token": self.access_token
        }
        try:
            resp_data = send_http_request(refresh_token_url, refresh_api_token_method, None, json.dumps(data))
            self.api_token = resp_data['jwt']
        except Exception as e:
            logging.info(str(e))

    def update_task_by_uuid(self, task_uuid: str, miner_fid: str, csv):
        update_task_url_suffix = '/uuid_tasks/'
        update_task_method = 'PUT'
        update_task_url = self.api_url + update_task_url_suffix + task_uuid
        payload_data = {"miner_fid": miner_fid}

        send_http_request(update_task_url, update_task_method, self.api_token, payload_data, file=csv)
        logging.info('Swan task updated.')

    def post_task(self, task: SwanTask, csv):
        logging.info('Creating new Swan task: %s' % task.task_name)
        create_task_url_suffix = '/tasks'
        create_task_method = 'POST'

        create_task_url = self.api_url + create_task_url_suffix
        payload_data = task.to_request_dict()

        send_http_request(create_task_url, create_task_method, self.api_token, payload_data, file=csv)
        logging.info('New Swan task Generated.')


    def update_miner(self, miner: Miner):
        update_miner_url_suffix = '/miners/%s/status' % miner.miner_id
        update_miner_method = 'PUT'

        update_miner_url = self.api_url + update_miner_url_suffix
        payload_data = json.dumps(miner.to_request_dict())

        return send_http_request(update_miner_url, update_miner_method, self.api_token, payload_data)

    def get_offline_deals(self, miner_fid: str, status: str, limit: int):
        url = self.api_url + "/offline_deals/" + miner_fid + "?deal_status=" + status + "&limit=" + limit + "&offset=0"

        get_offline_deals_method = "GET"
        try:
            response = send_http_request(url, get_offline_deals_method, self.api_token, None)
            return response["deal"]
        except Exception as e:
            return e

    def update_offline_deal_status(self, status: str, note: str, task_id: str, deal_cid: str):
        url = self.api_url + "/my_miner/tasks/" + task_id + "/deals/" + deal_cid
        update_offline_deal_status_method = "PUT"
        body = {"status": status, "note": note}

        send_http_request(url, update_offline_deal_status_method, self.api_token, body)

    def update_offline_deal_details(self, status: str, note: str, deal_id, file_path=None, file_size=None):
        url = self.api_url + "/my_miner/deals/" + str(deal_id)
        update_offline_deal_details_method = "PUT"
        body = {"status": status, "note": note, "file_path": file_path, "file_size": file_size}

        send_http_request(url, update_offline_deal_details_method, self.api_token, body)


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
            raise Exception("response code %s, %s" % (r.status_code, json.loads(r.text).get("message")))
        else:
            json_body = r.json()
            if json_body['status'] != 'success' and json_body['status'] != 'Success':
                raise Exception("response status failed.　%s." % json_body.get("message"))
            else:
                return json_body['data']
