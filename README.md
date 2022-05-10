# yape
Yet another python environment manager (One with less opinions)

## Alpha

### Install

The name "yape" was taken. Oh well. To install,

```shell
pip install yapenv
```

## Configuration options

### Core config
```yaml
python_version: '3.9' # The python version
python_executable: null # Overrides python_version
venv_directory: .venv # The venv path
environments: [] # Possible environments, see environment configs
pip_config_path: null # The path to the pip.conf to use.

# [Any environment config argument is also valid]
```
### Environment config

```yaml
env_file: .env # The env file to load when running commands.
pip_install_args: [] # List of arguments for pip install
virtualenv_args: [] # list of arguments for virtualenv.
requirements: [] # List of requirements, see requirement config (or string)
```

### Requirement config
```yaml
pacakge: null or str # Name of package.
import: null or str # Path to import (requirements.txt)
```