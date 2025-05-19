import logging
import sys

def setup_logger():
    logger = logging.getLogger("feedmill")
    logger.setLevel(logging.INFO)  # Для отладки можно поменять на DEBUG

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s"
    ))

    if not logger.handlers:
        logger.addHandler(handler)
    return logger

logger = setup_logger()
