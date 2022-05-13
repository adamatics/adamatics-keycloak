# -*- coding: utf-8 -*-

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    reqs = fh.read().split("\n")

with open("dev-requirements.txt", "r") as fh:
    dev_reqs = fh.read().split("\n")

setup(
    name="adamatics-keycloak",
    version="0.27.0",
    url="https://github.com/ryshoooo/python-keycloak",
    license="The MIT License",
    author="Marcos Pereira, Richard Nemeth",
    author_email="marcospereira.mpj@gmail.com,ryshoooo@gmail.com",
    keywords="keycloak openid oidc",
    description="adamatics-keycloak is a Python package providing access to the Keycloak API, "
    + "forked from the python-keycloak package.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["keycloak"],
    install_requires=reqs,
    tests_require=dev_reqs,
    python_requires=">=3.7",
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
