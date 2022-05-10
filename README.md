# yapenv
Yet another (less opinionated) python environment

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
python_executable: null # Overrides python_version
venv_directory: .venv # Virtualenv path
environments: [] # Possible environments, see environment configs
pip_config_path: null # Path to the pip.conf to use.

# [Any environment configuration argument is also valid]
```
### Environment Configuration

```yaml
env_file: .env # Env file to load when running commands.
pip_install_args: [] # List of arguments for pip install
virtualenv_args: [] # list of arguments for virtualenv.
requirements: [] # List of requirements, see requirement configuration (or string)
```

### Requirement Configuration

```yaml
package: null or str # Name of package.
import: null or str # Path to requirements.txt to import
```

### Environment Variables

- `VERSION_PATH`: File path to the `.version` file.
- `SETUP_VERSION`: Version string used by `setuptools.setup.version`.
- `YAPENV_ENV_FILE`: Env file to load when running commands (default=`.env`).
- `YAPENV_FULL_ERRORS`: Boolean that tells `yapenv` to dump full traceback (default=`"false"`).
- `YAPENV_CONFIG_FILES`: Array of yapenv config file names (default=`".yapenv.yaml .yapenv.yml .yapenv .yapenv.json"`).
- `NO_COLOR`: Boolean that disables colorized logging output (default="`false`")
- `VIRTUAL_ENV`: File path of python virtualenv (default=`None`)
- `SHELL`: Default command line shell.
    - Linux Default: `sh`
    - Windows Default: `cmd.exe`

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
- package: celery
- package: Flask
```
