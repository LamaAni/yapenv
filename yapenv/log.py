import os
import logging

NO_COLOR = os.environ.get("NO_COLOR", "false").lower() == "true"


class YAPENVLogFormatter(logging.Formatter):
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

    gray_format = "[%(asctime)s][yapenv][%(levelname)8s] %(message)s"
    color_format = "{gray}[%(asctime)s][yapenv]{end}{lvl_color}[%(levelname)8s]{end} %(message)s"

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


yapenv_log = logging.getLogger("yapenv_log")
yapenv_log.setLevel(logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO")))


# create console handler
yapenv_log_formatter = YAPENVLogFormatter()
yapenv_log_handler = logging.StreamHandler()
yapenv_log.addHandler(yapenv_log_handler)
yapenv_log_handler.setFormatter(yapenv_log_formatter)


if __name__ == "__main__":
    yapenv_log.info("Tester")
