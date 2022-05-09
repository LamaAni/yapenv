import os
import re

ENTRY_ENVS = os.environ.copy()
YAPE_CONFIG_FILES = re.split(r"[\s,]+", os.environ.get("YAPE_CONFIG_FILES", ".yape.yaml .yape .yape.yml .yape.json"))
