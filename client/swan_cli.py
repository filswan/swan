import argparse
import os
import random
import string

from task_sender.swan_task_sender import create_new_task


def random_hash(length=6):
    chars = string.ascii_lowercase + string.digits
    ran_hash = ''.join(random.choice(chars) for _ in range(length))
    return ran_hash


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Swan client')
    subparsers = parser.add_subparsers(title='task')

    task_parser = subparsers.add_parser('task')
    task_parser.add_argument('function', metavar='create', type=str, nargs=1, help='Create new Swan task')

    task_parser.add_argument('--config', dest='config_path', default="./config.toml",
                             help="Path to the config file (default: ./config.toml)")
    task_parser.add_argument('--name', dest='task_name', default="swan-task-" + random_hash(),
                             help="Task name (default: hash name)")
    task_parser.add_argument('--input', dest='input_dir', required=True,
                             help="Path to the dir of files ready to create a new task")

    args = parser.parse_args()

    if args.__getattribute__('function')[0] == 'create':
        input_dir = args.__getattribute__('input_dir')
        input_dir = os.path.abspath(input_dir)
        config_path = args.__getattribute__('config_path')
        config_path = os.path.abspath(config_path)
        task_name = args.__getattribute__('task_name')
        create_new_task(input_dir, config_path, task_name)
