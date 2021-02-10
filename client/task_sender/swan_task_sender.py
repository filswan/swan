import csv
import hashlib
import io
import os
import shutil
import sys
import time
from os import listdir
from os.path import isfile, join
from typing import List

import toml


def read_config(_config_path: str):
    if _config_path is None:
        _config_path = './config.toml'

    # script_dir = os.path.dirname(__file__)
    # file_path = os.path.join(script_dir, config_path)
    _config = toml.load(_config_path)

    return _config


def checksum(filename, hash_factory=hashlib.md5, chunk_num_blocks=128):
    h = hash_factory()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_num_blocks * h.block_size), b''):
            h.update(chunk)
    return h.hexdigest()


def read_file_path_in_dir(dir_path: str) -> List[str]:
    _file_paths = [join(dir_path, f) for f in listdir(dir_path) if isfile(join(dir_path, f))]
    return _file_paths


def generate_csv(_csv_data: List[dict]):
    with io.StringIO() as csv_file:
        fieldnames = ['miner_id', 'deal_cid', 'file_source_url', 'md5', 'start_epoch']
        csv_writer = csv.DictWriter(csv_file, delimiter=',', fieldnames=fieldnames)
        csv_writer.writeheader()
        for line in _csv_data:
            csv_writer.writerow(line)


def move_file(from_path: str, to_dir: str):
    filename = os.path.basename(from_path)
    _to_path = os.path.join(to_dir, filename)

    if os.path.isfile(_to_path):
        _to_path = _to_path + str(int(time.time()))
        filename = os.path.basename(_to_path)
    shutil.copyfile(from_path, _to_path)
    return _to_path


if __name__ == '__main__':
    input_path = sys.argv[1]
    if len(sys.argv) == 3:
        config_path = sys.argv[2]
    else:
        config_path = None
    config = read_config(config_path)
    output_dir = config['main']['output_dir']
    download_url_prefix = config['main']['download_url_prefix']
    is_public = config['main']['is_public']
    task_type = config['main']['task_type']
    generate_md5 = config['main']['generate_md5']

    file_paths = read_file_path_in_dir(input_path)

    csv_data_list = []

    for file_path in file_paths:
        target_file_path = move_file(file_path, to_dir=output_dir)
        target_file_name = os.path.basename(target_file_path)

        file_source_url = os.path.join(download_url_prefix, target_file_name)
        if generate_md5:
            md5 = checksum(target_file_path)
        else:
            md5 = ""

        csv_data = {'miner_id': "",
                    'deal_cid': "",
                    'file_source_url': file_source_url,
                    'md5': md5,
                    'start_epoch': ""
                    }
        csv_data_list.append(csv_data)
    generate_csv(csv_data_list)
