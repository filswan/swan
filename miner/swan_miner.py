import threading
import time
from swan_miner_deal_downloader import downloader
from swan_miner_deal_importer import importer
from swan_miner_deal_scanner import scanner


if __name__ == "__main__":
    swan_miner_downloader = threading.Thread(target=downloader)
    swan_miner_importer = threading.Thread(target=importer)
    swan_miner_scanner = threading.Thread(target=scanner)

    swan_miner_downloader.start()
    swan_miner_importer.start()
    swan_miner_scanner.start()