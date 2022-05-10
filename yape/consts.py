import os
import re

ENTRY_ENVS = os.environ.copy()
YAPE_CONFIG_FILES = re.split(r"[\s,]+", os.environ.get("YAPE_CONFIG_FILES", ".yape.yaml .yape .yape.yml .yape.json"))


def get_version():
    version_path = os.path.join(os.path.dirname(__file__), ".version")
    if os.path.isfile(version_path):
        with open(version_path, "r") as raw:
            return raw.read().strip()
    return "local"


YAPE_VERSION = get_version()
__version__ = YAPE_VERSION
