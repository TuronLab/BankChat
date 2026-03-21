import logging
import os


class ColorFormatter(logging.Formatter):
    # ANSI color codes
    COLORS = {
        logging.INFO:    "\033[0m",          # white / default
        logging.WARNING: "\033[33m",         # yellow
        logging.ERROR:   "\033[31m",         # red
        logging.CRITICAL:"\033[1;31m",       # bright red
    }
    RESET = "\033[0m"

    def format(self, record):
        # Pick color based on level
        color = self.COLORS.get(record.levelno, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"

def config_logger(log_file, used_by='MONITOR'):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger(used_by.lower() + "_logger")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if not logger.handlers:
        fmt = f'%(asctime)s - [{used_by}] - %(levelname)s - %(message)s'

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(fmt))

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColorFormatter(fmt))

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        logger.info(
            "Logger initialized for %s, logs will be stored into %s",
            used_by, os.path.dirname(log_file)
        )

    return logger

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.environ.get("LOG_PATH",  os.path.join(project_path, ".logs"))
CHAT_LOGGER = config_logger(os.path.join(LOG_PATH, "chat.log"), 'BANK_CHAT')

ASSETS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
