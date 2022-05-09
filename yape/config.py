import re
import yaml
import json
import os
import sys
from typing import Union, List, Dict
from yape.common import deep_merge, yape_log

YAPE_CONFIG_FILES = re.split(r"[\s,]+", os.environ.get("YAPE_CONFIG_FILES", ".yape .yape.yaml .yape.yml .yape.json"))


class YAPEPythonVersion(dict):
    @property
    def major(self) -> str:
        return self.get("major", None)

    @property
    def minor(self) -> str:
        return self.get("minor", None)

    @property
    def patch(self) -> str:
        return self.get("patch", None)

    @property
    def version(self) -> str:
        return ".".join(p for p in [self.major, self.minor, self.patch] if p is not None)

    def __str__(self):
        return self.version

    def __repr__(self) -> str:
        return self.version

    @classmethod
    def parse(cls, val: Union[str, float]):
        val = val or sys.version
        if not isinstance(val, str):
            val = str(val)
        # Parsing the version
        parts = val.split(".")
        ver = {}
        if len(parts) > 0:
            ver["major"] = parts[0]
        if len(parts) > 1:
            ver["minor"] = parts[1]
        if len(parts) > 2:
            ver["patch"] = parts[2]

        return YAPEPythonVersion(ver)


class YAPEConfigRequirement(dict):
    @property
    def package(self) -> str:
        return self.get("package", None)

    @package.setter
    def package(self, val: str):
        self["package"] = val

    @property
    def import_path(self) -> str:
        """A path to a requirements file to import (relative to config root)"""
        return self.get("import_path", self.get("import", None))

    @classmethod
    def parse(cls, requirement: Union[str, dict]):
        if isinstance(requirement, dict):
            return cls(requirement)

        assert isinstance(requirement, str), "Package dictionary must be a dict or string"
        return cls(package=requirement.strip())


class YAPEEnvironmentConfig(dict):
    @property
    def source_path(self) -> str:
        """The original path where the config was loaded (Overriden by load)"""
        return self.get("source_path", None)

    @source_path.setter
    def source_path(self, val: str):
        self["source_path"] = val

    @property
    def venv_directory(self) -> str:
        """The path of the virtual env directory"""
        return self.get("venv_directory", ".venv")

    @property
    def venv_path(self) -> str:
        if os.path.isabs(self.venv_directory):
            return self.venv_directory
        return os.path.abspath(os.path.join(os.path.dirname(self.source_path), self.venv_directory))

    @property
    def python(self) -> YAPEPythonVersion:
        """The version of python to use"""
        ver = self.get("python", None)
        if not isinstance(ver, YAPEPythonVersion):
            ver = YAPEPythonVersion.parse(ver)
            self["python"] = ver
        return ver

    @property
    def python_executable(self) -> str:
        """The path to the python executable to use"""
        return self.get("python_executable", None)

    @property
    def requirements(self) -> List[YAPEConfigRequirement]:
        """A list of pip requirements"""
        requirements = self.get("requirements", [])
        if any([not isinstance(r, YAPEConfigRequirement) for r in requirements]):
            requirements = [YAPEConfigRequirement.parse(r) for r in requirements]
            self["requirements"] = requirements
        return requirements

    @property
    def pip_install_args(self) -> List[str]:
        return self.get("pip_install_args", [])

    @property
    def venv_args(self) -> List[str]:
        return self.get("venv_args", [])

    def resolve_venv_path(self, *parts: List[str]):
        return os.path.abspath(os.path.join(self.venv_path, *parts))

    def initialize_requirements(self):
        """Resolves the internal requirement imports and cleans up the requirements list"""
        if len(self.requirements) == 0:
            return []

        resolved_requirements = []
        src_path = None if self.source_path is None else os.path.dirname(self.source_path)
        for req in self.requirements:
            if req.import_path is not None:
                req_abs_path = (
                    os.path.join(src_path, req.import_path) if not os.path.isabs(req.import_path) else req.import_path
                )

                if os.path.isfile(req_abs_path):
                    with open(req_abs_path, "r", encoding="utf-8") as req_file:
                        requirements_raw = req_file.read()

                    # Clean comments
                    requirements_raw = re.sub(r"[#].*", "", requirements_raw)
                    for req_as_str in requirements_raw.split("\n"):
                        req_as_str = req_as_str.strip()
                        if len(req_as_str) == 0:
                            continue
                        resolved_requirements.append(YAPEConfigRequirement.parse(req_as_str))

            elif req.package is not None:
                resolved_requirements.append(req)

        self["requirements"] = resolved_requirements

    def initialize(self):
        """Initializes the config"""
        self.initialize_requirements()

    def clean_duplicate_requirements(self):
        requirements: List[YAPEConfigRequirement] = [] + self.requirements  # Last counts
        requirements.reverse()
        cleaned = []
        matched = set()
        for r in requirements:
            pkg_name = re.match(r"^[\w._-]+", r.package.strip())
            if pkg_name is None:
                pkg_name = r.package
            else:
                pkg_name = pkg_name[0]
            if pkg_name in matched:
                continue
            matched.add(pkg_name)
            cleaned.append(r)

        cleaned.reverse()
        self["requirements"] = cleaned


class YAPEConfig(YAPEEnvironmentConfig):
    @property
    def install_path(self) -> str:
        """Where to install"""
        return self.get("install_path", None)

    @install_path.setter
    def install_path(self, val: str):
        self["install_path"] = val

    @property
    def environments(self) -> Dict[str, YAPEEnvironmentConfig]:
        return self.get("environments", {})

    @property
    def inherit(self) -> bool:
        return self.get("inherit", False)

    def stop_inheritance(self) -> bool:
        return self.inherit

    @classmethod
    def load(
        cls,
        config_path: str,
        environment: str = None,
        inherit_depth: int = -1,
        delete_environments: bool = True,
    ):
        """Loads the YAPE environment configuration and initializes it.

        Args:
            config_path (str): The path/file to load the config from.
            environment (str, optional): The configuration environment to use. Defaults to None.
            inherit_depth (int, optional): If true, inherits configuration from parent directories. Defaults to True.
        """
        if config_path.endswith("/"):
            config_path = config_path[:-1]

        config_path = os.path.abspath(config_path)

        merge_configs: List[YAPEConfig] = []
        inherit_stopped = False

        def load_config_from_file(filepath):
            """Loads a config into the list.
            Returns false if needs to stop loading.
            """
            nonlocal inherit_stopped
            config = None
            filepath = os.path.abspath(filepath)
            if not os.path.isfile(filepath):
                return

            with open(filepath, "r", encoding="utf-8") as config_file:
                if filepath.endswith(".yaml") or filepath.endswith(".yml"):
                    config = yaml.safe_load(config_file.read())
                else:
                    config = json.loads(config_file.read())

            if config is not None and isinstance(config, dict):
                config = YAPEConfig(config)
                config.source_path = filepath
                merge_configs.append(YAPEConfig(config))
                if config.stop_inheritance():
                    inherit_stopped = True

            return config

        config_filepath_groups: List[List[str]] = []

        if os.path.isfile(config_path):
            # If a direct file, this is not included in inheritance.
            load_config_from_file(config_path)
            config_path = os.path.dirname(config_path)

        install_path = config_path

        while not inherit_stopped:
            config_filepath_groups.append(
                [os.path.join(config_path, filename) for filename in YAPE_CONFIG_FILES],
            )
            parent_path = os.path.dirname(config_path)
            if parent_path is None or parent_path == config_path:
                break
            config_path = parent_path

        if inherit_depth is not None and inherit_depth > -1:
            config_filepath_groups = config_filepath_groups[0 : inherit_depth + 1]

        for fgroup in config_filepath_groups:
            for fpath in fgroup:
                load_config_from_file(fpath)

                if inherit_stopped:
                    break
            if inherit_stopped:
                break

        # reversing the config merge order
        merge_configs.reverse()

        for config in merge_configs:
            if environment is not None and environment in config.environments:
                deep_merge(config, config.environments[environment])
            config.initialize()

        merged = YAPEConfig(deep_merge({}, *merge_configs))

        if delete_environments and "environments" in merged:
            del merged["environments"]

        merged.initialize()
        merged.clean_duplicate_requirements()
        merged.install_path = os.path.abspath(merged.install_path or install_path)

        return merged
