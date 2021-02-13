import sys

from common.Miner import Miner
from common.config import read_config
from common.swan_client import SwanClient

if __name__ == '__main__':
    miner_id = sys.argv[1]

    miner = Miner(miner_id)
    miner.acquire_miner_info_cmd()

    config = read_config()
    api_key = config['main']['api_key']
    access_token = config['main']['access_token']

    client = SwanClient(api_key, access_token)
    client.update_miner(miner)
