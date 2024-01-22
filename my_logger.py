import logging
import os

logs_dir = "./data"

if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

log_filename = f"{logs_dir}/server_logs.log"

logging.basicConfig(
    filename=log_filename,
    level=logging.DEBUG,
    # encoding="utf-8",
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)
