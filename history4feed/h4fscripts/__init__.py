import logging
LOG_PRINT = 105

def newLogger(name: str) -> logging.Logger:
    # Configure logging
    logging.addLevelName(LOG_PRINT, "LOG")
    stream_handler = logging.StreamHandler()  # Log to stdout and stderr
    stream_handler.setLevel(logging.INFO)
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s [%(levelname)s] %(message)s",
        handlers=[stream_handler],
        datefmt='%d-%b-%y %H:%M:%S'
    )
    logger = logging.getLogger("history4feed")
    logger.print = lambda msg: logger.log(LOG_PRINT, msg)
    logger.print("=====================history4feed======================")

    return logger

logger = newLogger("h4f-logger")