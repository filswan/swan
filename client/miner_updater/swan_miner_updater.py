from common.Miner import Miner
from common.config import read_config
from common.swan_client import SwanClient


def update_miner_info(miner_id: str, config_path):
    miner = Miner(miner_id)
    miner.acquire_miner_info_cmd()

    config = read_config(config_path)
    api_url = config['main']['api_url']
    api_key = config['main']['api_key']
    access_token = config['main']['access_token']

    client = SwanClient(api_url, api_key, access_token)
    resp = client.update_miner(miner)
    print(resp)
