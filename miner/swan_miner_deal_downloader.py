import logging
import os
import sys

from apscheduler.schedulers.background import BackgroundScheduler

from aria2c import Aria2c
from aria2_service import check_download_status, start_downloading
import subprocess

from common.config import read_config

config = read_config()
MINER_FID = config['main']['miner_fid']
ARIA2_HOTS = config['aria2']['aria2_host']
ARIA2_PORT = config['aria2']['aria2_port']
ARIA2_SECRET = config['aria2']['aria2_secret']
ARIA_CONF = config['aria2']['aria2_conf']

client = Aria2c(ARIA2_HOTS, ARIA2_PORT, ARIA2_SECRET)
MAX_DOWNLOADING_TASKS = 10


def downloader():
    # subprocess.Popen(["aria2c", "--conf-path=" + ARIA_CONF])
    logging.info("Start check_download_status.... ")
    sched = BackgroundScheduler()
    sched.add_job(
        check_download_status,
        args=[client],
        trigger='cron',
        minute='*/1',
        hour='*'
    )
    sched.start()
    start_downloading(MAX_DOWNLOADING_TASKS, MINER_FID, client)
