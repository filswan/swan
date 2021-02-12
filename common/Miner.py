import logging
import re
import subprocess
from decimal import Decimal


class Miner:
    miner_id: str = None
    price: Decimal = None
    verified_price: Decimal = None
    min_piece_size: str = None
    max_piece_size: str = None

    def __init__(self, miner_id):
        self.miner_id = miner_id

    def to_request_dict(self):
        return {
            'price': str(self.price),
            'verified_price': str(self.verified_price),
            'min_piece_size': self.min_piece_size,
            'max_piece_size': self.max_piece_size
        }

    def acquire_miner_info_cmd(self):
        try:
            proc = subprocess.check_output(['lotus', 'client', 'query-ask', self.miner_id], timeout=60,
                                           stderr=subprocess.PIPE)
        except subprocess.TimeoutExpired:
            logging.info('miner %s timeout' % self.miner_id)
            return
        except Exception as e:
            logging.error(e)
            if 'ERROR: bls signature failed to verify' in e.stderr.rstrip().decode('utf-8'):
                return
            else:
                logging.warning('lotus query-ask process not success, cause %s.' % str(e))
                return

        if proc is None:
            return
        else:
            lines = proc.rstrip().decode('utf-8').split('\n')
            for line in lines:
                logging.info('----- info: %s' % line)
                price_match = re.findall(r'''^Price per GiB: ([0-9]*\.?[0-9]+) FIL''', line)
                if len(price_match) != 0:
                    self.price = Decimal(price_match[0])

                verified_price_match = re.findall(r'''^Verified Price per GiB: ([0-9]*\.?[0-9]+) FIL''', line)
                if len(verified_price_match) != 0:
                    self.verified_price = Decimal(verified_price_match[0])

                min_piece_size_match = re.findall(r'''^Min Piece size: ([0-9]*\.?[0-9]+ [B|KiB|MiB|GiB]+)''', line)
                if len(min_piece_size_match) != 0:
                    self.min_piece_size = min_piece_size_match[0]

                max_piece_size_match = re.findall(r'''^Max Piece size: ([0-9]*\.?[0-9]+ [B|KiB|MiB|GiB]+)''', line)
                if len(max_piece_size_match) != 0:
                    self.max_piece_size = max_piece_size_match[0]
