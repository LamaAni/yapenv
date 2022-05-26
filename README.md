# yapenv

## Alpha

WARNING: This repo is still in alpha development phase and structure is subject to change.

Yet Another Python Environment manager (with less options).

### Features

1. Easy configuration via YAML files with optional inheritance.
1. Named environments with per-environment configuration (test, dev, beta, prod, etc...).
1. CLI interface with easy initialization.

NOTE: `yapenv` uses the package [bole](https://github.com/LamaAni/bole) to handle configuration and logging

## Install

```shell
pip install yapenv
```

Run in your project directory

```
yapenv init
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
inherit: false # Boolean, if true inherit parent directory's yapenv configuration
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

## Extra config and reading configuration values

yapenv allows extra configuration values to be embedded in its config file. e.g.

```yaml
python_version: "3.10"
venv_directory: .venv
requirements:
 - black
 - flake8

my_custom_config:
  a_list: 
    - a_key: "my_custom_value"
```

Note: extra configuration values follow yapenv config inheritance rules.

You can read your configuration value by,
```shell
yapenv config "my_custom_config.a_list[0].a_key"
```
That should output `my_custom_value`

Or a yaml block (see format options in the command),
```shell
yapenv config "my_custom_config.a_list"
```
Should output,
```yaml
- a_key: "my_custom_value"
```

# Contribution

Feel free to ping me in issues or directly on LinkedIn to contribute.

# Future implementation

We plan to support multiple python version per environment.

Looking for help on this subject.

# License

Copyright ©
`Zav Shotan`, `Patrick Huber`, and other [contributors](graphs/contributors).
It is free software, released under the MIT licence, and may be redistributed under the terms specified in `LICENSE`.
