import os
import re

ENTRY_ENVS = os.environ.copy()
YAPENV_CONFIG_FILES = re.split(
    r"[\s,]+",
    os.environ.get("YAPENV_CONFIG_FILES", ".yapenv.yaml .yapenv.yml .yapenv .yapenv.json"),
)


def get_version():
    """Return the yapenv version"""
    version_path = os.path.join(os.path.dirname(__file__), ".version")
    if os.path.isfile(version_path):
        with open(version_path, "r") as raw:
            return raw.read().strip()
    return "local"


YAPENV_VERSION = get_version()
__version__ = YAPENV_VERSION
