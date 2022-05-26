import tempfile
import yapenv.commands as yapenv_commands
from yapenv.config import YAPENVConfig


def test_init():
    with tempfile.TemporaryDirectory() as temp_dir_path:
        config = YAPENVConfig.load(temp_dir_path)
        yapenv_commands.init(config)


def test_install():
    with tempfile.TemporaryDirectory() as temp_dir_path:
        config = YAPENVConfig.load(temp_dir_path)
        yapenv_commands.install(config, reset=True, force=True)


def test_delete():
    with tempfile.TemporaryDirectory() as temp_dir_path:
        config = YAPENVConfig.load(temp_dir_path)
        yapenv_commands.install(config, reset=True, force=True)
        yapenv_commands.delete(config, force=True)
