import os
import logging

NO_COLOR = os.environ.get("NO_COLOR") == "true"


class YAPELogFormatter(logging.Formatter):
    colors = {
        "red": "\033[0;31m",
        "green": "\033[0;32m",
        "yellow": "\033[0;33m",
        "blue": "\033[0;34m",
        "magenta": "\033[0;35m",
        "cyan": "\033[0;36m",
        "gray": "\033[0;90m",
        "end": "\033[0m",
    }

    gray_format = "[%(asctime)s][%(levelname)8s] %(message)s"
    color_format = "{gray}[%(asctime)s]{end}{lvl_color}[%(levelname)8s]{end} %(message)s"

    FORMATS = {
        logging.DEBUG: "gray",
        logging.INFO: "green",
        logging.WARNING: "yellow",
        logging.ERROR: "red",
        logging.CRITICAL: "red",
    }

    def format(self, record):
        active_format = self.color_format if not NO_COLOR else self.gray_format
        lvl_color = self.colors[self.FORMATS.get(record.levelno, "gray")]
        active_format = active_format.format(lvl_color=lvl_color, **self.colors)
        formatter = logging.Formatter(active_format)
        return formatter.format(record)


yape_log = logging.getLogger("yape_log")
yape_log.setLevel(logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO")))


# create console handler
yape_log_formatter = YAPELogFormatter()
yape_log_handler = logging.StreamHandler()
yape_log.addHandler(yape_log_handler)
yape_log_handler.setFormatter(yape_log_formatter)


if __name__ == "__main__":
    yape_log.info("Tester")
