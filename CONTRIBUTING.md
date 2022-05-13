# Contributing

Welcome to the Adamatics Keycloak contributing guidelines. We are all more than happy to receive
any contributions to the repository and want to thank you in advance for your contributions!
This document outlines the process and the guidelines on how contributions work for this repository.

## Setting up the dev environment

The development environment is mainly up to the developer. Our recommendations are to create a python
virtual environment and install the necessary requirements. Example

```sh
python -m venv venv
source venv/bin/active
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m pip install -r dev-requirements.txt
```

## Running checks and tests

We're utilizing `tox` for most of the testing workflows. However we also have an external dependency on `docker`.
We're using docker to spin up a local keycloak instance which we run our test cases against. This is to avoid
a lot of unnecessary mocking and yet have immediate feedback from the actual Keycloak instance. All of the setup
is done for you with the tox environments, all you need is to have both tox and docker installed
(`tox` is included in the `dev-requirements.txt`).

To run the unit tests, simply run

```sh
tox -e tests
```

The project is also adhering to strict linting (flake8) and formatting (black + isort). You can always check that
your code changes adhere to the format by running

```sh
tox -e check
```

If the check fails, you'll see an error message specifying what went wrong. To simplify things, you can also run

```sh
tox -e apply-check
```

which will apply isort and black formatting for you in the repository. The flake8 problems however need to be resolved
manually by the developer.

## Conventional commits

Commits to this project must adhere to the [Conventional Commits
specification](https://www.conventionalcommits.org/en/v1.0.0/) that will allow
us to automate version bumps and changelog entry creation.

After cloning this repository, you must install the pre-commit hook for
conventional commits (this is included in the `dev-requirements.txt`)

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install pre-commit
pre-commit install --install-hooks -t pre-commit -t pre-push -t commit-msg
```

## How to contribute

1. Fork this repository, develop and test your changes
2. Make sure that your changes do not decrease the test coverage
3. Make sure you're commits follow the conventional commits
4. Submit a pull request

## How to release

The CICD pipelines are set up for the repository. When a PR is merged, a new version of the library
will be automatically deployed to the PyPi server, meaning you'll be able to see your changes immediately.
