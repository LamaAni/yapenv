import json
import os
from typing import List
import yaml
from yape.consts import YAPE_CONFIG_FILES
from yape.config import YAPEConfig
from yape.utils import deep_merge, resolve_template, touch


def init(
    active_config: YAPEConfig,
    config_filename: str = None,
    python_version: str = None,
    merge_with_current: bool = False,
    add_requirement_files: bool = True,
):
    # Checking configuration
    to_merge: List[YAPEConfig] = []
    to_merge.append(
        YAPEConfig.load(
            resolve_template("config.yaml"),
            inherit_depth=0,
            resolve_imports=False,
            delete_environments=False,
            clean_duplicate_requirements=False,
        )
    )
    if add_requirement_files:
        to_merge.append(
            YAPEConfig.load(
                resolve_template("config_with_requirements.yaml"),
                inherit_depth=0,
                resolve_imports=False,
                delete_environments=False,
                clean_duplicate_requirements=False,
            )
        )

    if merge_with_current:
        to_merge.append(active_config)

    config = YAPEConfig(deep_merge({}, *to_merge))
    config.initialize(resolve_imports=False)

    if python_version is not None:
        config.python_version = python_version

    # Deleting invalid keys
    def del_key(key: str):
        if key in config:
            del config[key]

    del_key("source_path")
    del_key("source_directory")
    if config.python_executable in config:
        del_key("python_version")

    config_filename = config_filename or YAPE_CONFIG_FILES[0] or ".yape.yaml"
    with open(os.path.join(active_config.source_directory, config_filename), "w") as config_file:
        if config_filename.endswith(".json"):
            config_file.write(json.dumps(config.to_dictionary(), indent=2))
        else:
            config_file.write(yaml.safe_dump(config.to_dictionary()))

    if add_requirement_files:
        touch(os.path.join(active_config.source_directory, "requirements.txt"))
        touch(os.path.join(active_config.source_directory, "requirements.dev.txt"))
