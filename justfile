play: czytaj

mnoz:
	poetry run mnozenie

czytaj:
   #!/bin/bash
   cd kot_w_butach
   poetry run czytanie


# Installs pre-commit hooks (and pre-commit if it is not installed)
install-hooks: install-pre-commit
  #!/usr/bin/env bash
  set -euo pipefail
  if [ ! -f .git/hooks/pre-commit ]; then
    pre-commit install
  fi

[private]
install-pre-commit:
  #!/usr/bin/env bash
  set -euo pipefail
  # Check if command pre-commit is available. If yes - exists
  if command -v pre-commit &> /dev/null; then
    exit 0
  fi
  # Check if pipx exists. If it does not, asks
  if ! command -v pipx &> /dev/null; then
    echo "pipx is not installed. It is recommended to install pre-commit using pipx rather than pip. Please install pipx using `pip install pipx` and try again."
    exit 1
  fi
  pipx install pre-commit

# Runs the pre-commit checks. "all" runs checks on all files, not only the dirty ones.
check arg="dirty": install-pre-commit
  #!/usr/bin/env bash
  set -euo pipefail
  if [[ "{{arg}}" == "all" ]]; then
    pre-commit run --all-files
  else
    pre-commit run
  fi

# Downloads dependencies and installs the git commit hooks
setup: install-hooks get-poetry run-poetry

# Updates the .secrets.baseline file with the latest secrets. Please run it only when you are sure, that no actual secrets are present in the repository.
update-secrets:
    #!/usr/bin/env bash
    set -euo pipefail
    # Check for detect-secrets installation
    if ! which detect-secrets &> /dev/null; then
        echo "detect-secrets is not installed."
        if ! which pipx &> /dev/null; then
            echo "pipx is also not installed. It is recommended to install detect-secrets using pipx rather than pip. Please install pipx and try again."
            exit 1
        fi
        pipx install detect-secrets
    fi

    detect-secrets scan > .secrets.baseline
    echo "Updated .secrets.baseline file with the latest secrets."

# Makes sure poetry is installed
get-poetry:
    #!/usr/bin/env bash
    set -euo pipefail
    if ! command -v poetry &> /dev/null; then
        if ! command -v pipx &> /dev/null; then
            echo "Poetry is not installed. Please install poetry using the instructions at https://python-poetry.org/docs/#installation."
            exit 1
        fi
        echo "Poetry is not installed. Installing poetry using pipx."
        pipx install poetry
    fi


run-poetry:
    #!/usr/bin/env bash
    set -euo pipefail
    poetry install
    echo "You are now inside the poetry shell. To exit the shell, type 'exit'."
    echo "Try these new commands provided by this repository:"
    echo
    echo "$ setup_data - Downloads and sets up a given scenario."
    poetry shell

check-all:
    #!/bin/bash
    pre-commit run --all-files
