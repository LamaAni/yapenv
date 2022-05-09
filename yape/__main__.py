import os

ENTRY_ENVS = os.environ.copy()

from yape import common

common.ENTRY_ENVS = ENTRY_ENVS

from yape.cli import yape

if __name__ == "__main__":
    yape()
