import os
import re
from setuptools import setup, find_packages
import logging

repo_dir = os.path.dirname(os.path.abspath(__file__))

# Get the long description from the README file
with open(os.path.join(repo_dir, "README.md"), "r") as readme:
    long_description = readme.read()


with open(os.path.join(repo_dir, "requirements.txt"), "r") as requirements_file:
    requirements_text = requirements_file.read()
    requirements_text = re.sub(r"[#].*", "", requirements_text)
    requirement_list = [r.strip() for r in requirements_text.split("\n") if len(r.strip()) > 0]

version_file_path = os.path.join(os.path.dirname(__file__), ".version")
version = None
if os.path.isfile(version_file_path):
    with open(version_file_path, "r") as file:
        version = file.read()
else:
    logging.info("Version file not found @ " + version_file_path)
    logging.info("Using default version debug")

version = version or "debug"

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.
GITHUB_URL = "https://github.com/LamaAni/yape.git"

packages = find_packages()
print(packages)

setup(
    name="yapenv",  # Required
    version=version,  # Required
    description="Yet another python environment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=GITHUB_URL,
    author="Zav Shotan",
    keywords="environment, venv, virtualenv, pyenv, poetry",
    packages=packages,
    entry_points={
        "console_scripts": [
            "yape=yape.__main__:run_cli_main",
            "yapenv=yape.__main__:run_cli_main",
        ],
    },
    install_requires=requirement_list,
    project_urls={
        "Source": GITHUB_URL,
    },
)
