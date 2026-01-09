import logging
import datetime
import os

# TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
TS = datetime.datetime.now().strftime("%Y%m%d")
formatter = logging.Formatter(
    "%(asctime)s, %(levelname)s, %(filename)s, %(funcName)s: %(message)s"
)


def logger(name: str, level=logging.INFO):
    log_file = f"./logs/logger_{TS}.log"
    if not os.path.exists("./logs"):
        os.mkdir("./logs")

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger_custom = logging.getLogger(name)
    logger_custom.setLevel(level)
    logger_custom.addHandler(file_handler)
    logger_custom.addHandler(stream_handler)

    return logger_custom
