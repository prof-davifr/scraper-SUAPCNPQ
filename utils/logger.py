import logging
from pathlib import Path

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("suap_scraper")
logger.setLevel(logging.INFO)

fh = logging.FileHandler("logs/run.log", mode="a", encoding="utf-8")
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%H:%M')
fh.setFormatter(formatter)
logger.addHandler(fh)

def log_msg(msg):
    logger.info(msg)
    print(msg)
