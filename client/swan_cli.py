import argparse
import os
import random
import string

from task_sender.deal_sender import send_deals
from task_sender.swan_task_sender import create_new_task


def random_hash(length=6):
    chars = string.ascii_lowercase + string.digits
    ran_hash = ''.join(random.choice(chars) for _ in range(length))
    return ran_hash


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Swan client')

    parser.add_argument('function', metavar='task/deal', choices=['task', 'deal'], type=str, nargs="?",
                        help='Create new Swan task/Send deal')

    parser.add_argument('--config', dest='config_path', default="./config.toml",
                        help="Path to the config file (default: ./config.toml)")

    parser.add_argument('--name', dest='task_name', default="swan-task-" + random_hash(),
                        help="Task name (default: hash name)")
    parser.add_argument('--input', dest='input_dir', help="Path to the dir of files ready to create a new task")

    parser.add_argument('--miner', dest='miner_id', help="Miner ID to send deals to.")
    parser.add_argument('--csv', dest='metadata_csv_path', help="The CSV file path of deal metadata.")

    args = parser.parse_args()

    if args.__getattribute__('function') == 'task':
        input_dir = args.__getattribute__('input_dir')
        if not input_dir:
            print('Please provide --input')
            exit(1)
        input_dir = os.path.abspath(input_dir)
        config_path = args.__getattribute__('config_path')
        config_path = os.path.abspath(config_path)
        task_name = args.__getattribute__('task_name')

        create_new_task(input_dir, config_path, task_name)
    elif args.__getattribute__('function') == "deal":
        config_path = args.__getattribute__('config_path')
        config_path = os.path.abspath(config_path)
        metadata_csv_path = args.__getattribute__('metadata_csv_path')
        if not metadata_csv_path:
            print('Please provide --csv')
            exit(1)
        metadata_csv_path = os.path.abspath(metadata_csv_path)
        miner_id = args.__getattribute__('miner_id')
        if not miner_id:
            print('Please provide --miner')
            exit(1)

        send_deals(config_path, miner_id, metadata_csv_path)
