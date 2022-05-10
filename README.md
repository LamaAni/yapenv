# yapenv
### Yet Another Python Environment manager
###### * with less opinions

## Install

```shell
pip install yapenv
```

## Configuration

By default `yapenv` uses the following configuration file names.

- `.yapenv.yaml`
- `.yapenv.yml`
- `.yapenv`
- `.yapenv.json`

### Core Configuration

```yaml
python_version: "3.9" # Python version to use
python_executable: null # Path to python executable (overrides python_version)
venv_directory: .venv # Path to created virtualenv directory
pip_config_path: null # Path to the pip.conf file
inherit: false # Boolean, if true inherit parent directory's yapenv configuration file
environments: [] # Optional environments, see environment configs

# These values are inherited from and overwritten by environment configuration
env_file: .env # Env file to load when running commands
pip_install_args: [] # List of arguments for pip install command
virtualenv_args: [] # list of arguments for virtualenv command
requirements: [] # List of requirements (see requirement configuration)
```
### Environment Configuration

Enabled by using `--env <environment_name>` argument.

```yaml
environments:
  dev: # Environment name
    env_file: .env # Env file to load when running commands
    pip_install_args: [] # List of arguments for pip install command
    virtualenv_args: [] # list of arguments for virtualenv command
    requirements: [] # List of requirements (see requirement configuration)
```

### Requirement Configuration

```yaml
requirements:
- package: mypackage # Pip package name string
- myotherpackage==0.0.1 # Pip package name string
- import: requirements.txt # Path to requirements.txt to import
```

### Environment Variables

- `YAPENV_ENV_FILE`: Env file to load when running commands (default=`.env`).
- `YAPENV_FULL_ERRORS`: Boolean that tells `yapenv` to dump full traceback (default=`"false"`).
- `YAPENV_CONFIG_FILES`: Array of yapenv config file names (default=`".yapenv.yaml .yapenv.yml .yapenv .yapenv.json"`).
- `NO_COLOR`: Boolean that disables colorized logging output (default="`false`")
- `VIRTUAL_ENV`: File path of python virtualenv (default=`None`)

### Example Configurations

#### Requirements File Method
```
python_version: "3.9"
venv_directory: .venv
environments:
  dev:
    requirements:
    - import: requirements.dev.txt
requirements:
- import: requirements.txt
```

#### Package List Method
```
python_version: "3.10"
venv_directory: .venv
environments:
  dev:
    requirements:
    - package: flake8
    - package: black
requirements:
- package: celery==5.2.6
- Flask>=2.1.2
```
