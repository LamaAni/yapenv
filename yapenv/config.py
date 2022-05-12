import re
import yaml
import json
import os
import sys
from typing import Any, Union, List, Dict
from yapenv.consts import YAPENV_CONFIG_FILES
from yapenv.utils import deep_merge, resolve_path, get_collection_path, clean_data_types
from yapenv.log import yapenv_log


REQUIREMENTS_COLLECTION_NAME = "requirements"


class YAPENVConfigRequirement(dict):
    @property
    def package(self) -> str:
        """The name of the package to require"""
        return self.get("package", None)

    @package.setter
    def package(self, val: str):
        self["package"] = val

    @property
    def import_path(self) -> str:
        """A path to a requirements file to import (relative to config root)"""
        return self.get("import_path", self.get("import", None))

    @classmethod
    def parse(cls, requirement: Union[str, dict, "YAPENVConfigRequirement"]):
        """Parse the string/dict and return the package requirement"""
        if isinstance(requirement, cls):
            return requirement
        if isinstance(requirement, dict):
            return cls(requirement)

        assert isinstance(requirement, str), "Package dictionary must be a dict or string"
        return cls(package=requirement.strip())

    @classmethod
    def unique(cls, requirements: List[Union["YAPENVConfigRequirement", dict]]):
        """Removes duplicate requirements and validates a requirement list."""
        requirements = [YAPENVConfigRequirement.parse(r) for r in requirements]
        requirements.reverse()
        cleaned = []
        matched = set()
        for r in requirements:
            if r.import_path is not None:
                pkg_name = "import: " + r.import_path
            else:
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
        return cleaned


class YAPENVEnvironmentConfig(dict):
    @property
    def source_path(self) -> str:
        """The original path where the config was loaded (Overriden by load)"""
        return self.get("source_path", None)

    @source_path.setter
    def source_path(self, val: str):
        self["source_path"] = val

    @property
    def env_file(self) -> str:
        return self.get("env_file", ".env")

    @property
    def requirements(self) -> List[YAPENVConfigRequirement]:
        """A list of pip requirements"""
        requirements = self.get(REQUIREMENTS_COLLECTION_NAME, [])
        if any([not isinstance(r, YAPENVConfigRequirement) for r in requirements]):
            requirements = [YAPENVConfigRequirement.parse(r) for r in requirements]
            self[REQUIREMENTS_COLLECTION_NAME] = requirements
        return requirements

    @property
    def pip_install_args(self) -> List[str]:
        return self.get("pip_install_args", [])

    @property
    def virtualenv_args(self) -> List[str]:
        return self.get("virtualenv_args", [])

    def to_dictionary(self) -> dict:
        """Convert this config to a dictionary"""
        return clean_data_types(self)

    def search(self, *paths: str) -> List[Any]:
        """Search the config for specific dictionary paths.
        Paths is a list of string representations of dictionary paths.
        Ex: paths = ['a.b[0].c']
        """
        return [get_collection_path(self, p) for p in paths]

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
                        resolved_requirements.append(YAPENVConfigRequirement.parse(req_as_str))

            elif req.package is not None:
                resolved_requirements.append(req)

        self[REQUIREMENTS_COLLECTION_NAME] = resolved_requirements

    def initialize(
        self,
        resolve_imports: bool = True,
    ):
        """Initializes the config"""
        if resolve_imports:
            self.initialize_requirements()


class YAPENVConfig(YAPENVEnvironmentConfig):
    @property
    def source_directory(self) -> str:
        """The directory path to the source for the virtual environment (where the config is)"""
        return self.get("source_directory", None)

    @source_directory.setter
    def source_directory(self, val: str):
        self["source_directory"] = val

    @property
    def venv_directory(self) -> str:
        """The path of the virtual env directory"""
        return self.get("venv_directory", ".venv")

    @property
    def venv_path(self) -> str:
        """The path to the virtual environment"""
        if os.path.isabs(self.venv_directory):
            return self.venv_directory
        return os.path.abspath(os.path.join(self.source_directory, self.venv_directory))

    @property
    def pip_config_path(self) -> str:
        return self.get("pip_config_path", None)

    @property
    def python_version(self) -> str:
        return self.get("python_version", f"{sys.version_info.major}.{sys.version_info.minor}")

    @python_version.setter
    def python_version(self, val: str):
        self["python_version"] = val

    @property
    def python_executable(self) -> str:
        """The path to the python executable to use"""
        return self.get("python_executable", None)

    def resolve_from_venv_directory(self, *parts: List[str]):
        """Resolve path with the virtual env directory as root path"""
        return resolve_path(*parts, root_directory=self.venv_path)

    def resolve_from_source_directory(self, *parts: List[str]):
        """Resolve path with the source directory as root path"""
        return resolve_path(*parts, root_directory=self.source_directory)

    @property
    def environments(self) -> Dict[str, YAPENVEnvironmentConfig]:
        """A dictionary of the configuration environments available"""
        return self.get("environments", {})

    @property
    def inherit(self) -> bool:
        """If true, this config can inherit its parents"""
        return self.get("inherit", False)

    def stop_inheritance(self) -> bool:
        """If returns true, stops any further inheritance.
        Overrideable function.
        """
        if self.inherit is not True:
            return True
        return False

    def load_virtualenv(self):
        """Loads the virtual environment into python (using activate.py)."""
        import importlib.util

        import_path = self.resolve_from_venv_directory("bin", "activate_this.py")
        assert os.path.isfile(import_path), "Virtual env not found or virtualenv invalid @ " + self.venv_path
        spec = importlib.util.spec_from_file_location(re.sub(r"[^\w]+", "_", import_path), import_path)
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)

    def initialize(
        self,
        source_directory: str = None,
        resolve_imports: bool = True,
        clean_duplicate_requirements: bool = True,
    ):
        """Initialize and clean the configuration"""
        super().initialize(
            resolve_imports=resolve_imports,
        )

        if clean_duplicate_requirements:
            self.clean_duplicate_requirements()

        if source_directory:
            self.source_directory = os.path.abspath(self.source_directory or source_directory)

    def clean_duplicate_requirements(self):
        """Clean all duplicate requirement entries"""
        configs = [self] + list(self.environments.values())
        for c in configs:
            if REQUIREMENTS_COLLECTION_NAME in c:
                c[REQUIREMENTS_COLLECTION_NAME] = YAPENVConfigRequirement.unique(c[REQUIREMENTS_COLLECTION_NAME])

    def has_virtual_environment(self) -> dict:
        """True if a virtual environment exists"""
        return os.path.isdir(self.venv_path)

    @classmethod
    def load(
        cls,
        config_path: str,
        environment: str = None,
        inherit_depth: int = -1,
        delete_environments: bool = True,
        resolve_imports: bool = True,
        clean_duplicate_requirements: bool = True,
    ):
        """Loads the YAPENV environment configuration and initializes it.

        Args:
            config_path (str): The path/file to load the config from.
            environment (str, optional): The configuration environment to use. Defaults to None.
            inherit_depth (int, optional): If true, inherits configuration from parent directories. Defaults to True.
        """
        if config_path.endswith("/"):
            config_path = config_path[:-1]

        config_path = os.path.abspath(config_path)
        yapenv_log.debug("Reading configuration, starting from " + config_path)

        merge_configs: List[YAPENVConfig] = []
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
                config = YAPENVConfig(config)
                config.source_path = filepath
                merge_configs.append(YAPENVConfig(config))
                if config.stop_inheritance():
                    inherit_stopped = True

            yapenv_log.debug("Loaded config file: " + filepath)

            return config

        config_filepath_groups: List[List[str]] = []

        if os.path.isfile(config_path):
            # If a direct file, this is not included in inheritance.
            load_config_from_file(config_path)
            config_path = os.path.dirname(config_path)
            yapenv_log.debug("Config path was a file, loading parent directory config " + config_path)

        source_directory = config_path

        while not inherit_stopped:
            config_filepath_groups.append(
                [os.path.join(config_path, filename) for filename in YAPENV_CONFIG_FILES],
            )
            parent_path = os.path.dirname(config_path)
            if parent_path is None or parent_path == config_path:
                break
            config_path = parent_path

        if inherit_depth is not None and inherit_depth > -1:
            config_filepath_groups = config_filepath_groups[0 : inherit_depth + 1]  # noqa E203

        for fgroup in config_filepath_groups:
            for fpath in fgroup:
                load_config_from_file(fpath)

                if inherit_stopped:
                    break
            if inherit_stopped:
                break

        # reversing the config merge order
        merge_configs.reverse()

        environment_found = False

        for config in merge_configs:
            if environment is not None and environment in config.environments:
                environment_found = True
                deep_merge(config, config.environments[environment])

            config.initialize(resolve_imports=resolve_imports)

        assert environment is None or environment_found, ValueError(
            f"No environment named '{environment}' was found in the config (or parent configs)"
        )

        merged = YAPENVConfig(deep_merge({}, *merge_configs))

        if delete_environments and "environments" in merged:
            del merged["environments"]

        merged.initialize(
            source_directory=source_directory,
            resolve_imports=resolve_imports,
            clean_duplicate_requirements=clean_duplicate_requirements,
        )

        yapenv_log.debug("Configuration loaded")

        return merged
