# -*- coding: utf-8 -*-
import re
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    reqs = fh.read().split("\n")

with open("dev-requirements.txt", "r") as fh:
    dev_reqs = fh.read().split("\n")

with open("docs-requirements.txt", "r") as fh:
    docs_reqs = fh.read().split("\n")


VERSIONFILE = "keycloak/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

setup(
    name="adamatics-keycloak",
    version=verstr,
    url="https://github.com/adamatics/adamatics-keycloak",
    license="The MIT License",
    author="Marcos Pereira, Richard Nemeth",
    author_email="ryshoooo@gmail.com",
    keywords="keycloak openid oidc",
    description="adamatics-keycloak is a Python package providing access to the Keycloak API, "
    + "forked from the python-keycloak package.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["keycloak"],
    install_requires=reqs,
    tests_require=dev_reqs,
    extras_require={"docs": docs_reqs},
    python_requires=">=3.7",
    project_urls={
        "Documentation": "https://adamatics-keycloak.readthedocs.io/en/latest/",
        "Issue tracker": "https://github.com/adamatics/adamatics-keycloak/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Operating System :: MacOS",
        "Operating System :: Unix",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Utilities",
    ],
)
