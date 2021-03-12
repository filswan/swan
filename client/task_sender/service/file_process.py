import hashlib
import logging
import os
import re
import shutil
import subprocess
import time


def stage_one(input_path, output_path: str):
    piece_cid = generate_car(input_path, output_path)[0]
    data_cid = import_by_lotus(output_path)
    return [piece_cid, data_cid]


def generate_car(input_path, output_path: str):
    logging.info('Generating car file from: %s' % input_path)
    try:
        subprocess.check_output(['lotus', 'client', 'generate-car', input_path, output_path],
                                stderr=subprocess.PIPE)
    except Exception as e:
        print(e)
    return generate_piece_cid(output_path)


def import_by_lotus(file):
    # 1. import
    logging.info('Generating data CID....')
    proc = subprocess.Popen(['lotus', 'client', 'import', file], stdout=subprocess.PIPE)
    resp = proc.stdout.readline().rstrip().decode('utf-8')
    data_cid = resp.split("Root ")[1]
    logging.info('Data CID: %s' % data_cid)

    return data_cid


def generate_piece_cid(file_path: str):
    piece_cid: str = ''
    piece_size: str = ''
    try:
        proc = subprocess.check_output(['lotus', 'client', 'commP', file_path])
    except Exception as e:
        logging.error(e)
        exit(1)
    lines = proc.rstrip().decode('utf-8').split('\n')
    for line in lines:
        piece_cid_match = re.findall(r'''CID:  ([a-z0-9]+)''', line)
        if len(piece_cid_match) > 0:
            piece_cid = piece_cid_match[0]
        piece_size_match = re.findall(r'''Piece size:  ([0-9]*\.?[0-9]+ [B|KiB|MiB|GiB]+)''', line)
        if len(piece_size_match) > 0:
            piece_size = piece_size_match[0]
    logging.info('car file Generated: %s, piece cid: %s, piece size: %s' % (file_path, piece_cid, piece_size))
    return [piece_cid, piece_size]


def checksum(filename, hash_factory=hashlib.md5, chunk_num_blocks=128):
    logging.info('Calculating md5 for file %s' % filename)
    h = hash_factory()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_num_blocks * h.block_size), b''):
            h.update(chunk)

    _checksum = h.hexdigest()
    logging.info('Calculated md5 %s' % _checksum)
    return _checksum


def move_file(from_path: str, to_dir: str):
    filename = os.path.basename(from_path)
    _to_path = os.path.join(to_dir, filename)

    if os.path.isfile(_to_path):
        _to_path = _to_path + str(int(time.time()))
    shutil.copyfile(from_path, _to_path)
    return _to_path
