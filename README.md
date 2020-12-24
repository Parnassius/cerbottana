# cerbottana

[![Python 3.7.9](https://img.shields.io/badge/python-3.7.9-blue.svg)](https://www.python.org/downloads/release/python-379/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests status](https://img.shields.io/github/workflow/status/Parnassius/cerbottana/main/master?event=push&label=tests)](https://github.com/Parnassius/cerbottana/actions?query=workflow%3Amain)
[![Codecov](https://img.shields.io/codecov/c/gh/Parnassius/cerbottana/master?token=RYDAXOWCUS)](https://codecov.io/gh/Parnassius/cerbottana)

cerbottana is a [Pokémon Showdown](https://play.pokemonshowdown.com/) bot, originally developed for the room [Italiano](https://play.pokemonshowdown.com/italiano).

## Contributing

Before submitting a pull request, please make sure your code is linted with `pylint`, type-checked with `mypy`, formatted with `black` and `isort`. Also run `pytest` unit tests.

The bulk of cerbottana code is plugins (see [plugins reference](plugins/README.md)). Working on a simple plugin is a good first contribution.

## Detailed install instructions

### Creating the virtual environment and installing dependencies

These instructions assume you are in the root directory of a cloned cerbottana repository. If you use Windows, it is strongly advised to work within the [WSL](https://docs.microsoft.com/en-us/windows/wsl).

If you are going to test your bot locally, you will also need an active instance of a [Pokémon Showdown server](https://github.com/smogon/pokemon-showdown).

It is highly recommended to use a Python 3.7 virtual environment. Although newer versions should also work, they might cause inconsistencies in `pip-compile` output.

To create and start the virtual environment on Unix or MacOS, run:

    python3 -m venv .venv
    source .venv/bin/activate

Add the core dependencies needed to run an instance of the bot:

    pip3 install -r requirements.txt

If you wish to contribute, you will also need dev-tools:

    pip3 install -r requirements-dev.txt

The next sections assume that the virtual environment is still active. When you are done, simply run `deactivate` to exit.

### Generating complementary files

Copy `.env-example` into `.env` and edit the file accordingly. Optional environment variables are commented out.

Use ``alembic`` to generate the required SQLite databases:

    alembic upgrade head

You should run this command every time you make any change to the database schema. If you are not sure, just check if the ``alembic/`` folder has new files, and run the command if it does.

### Running a bot instance

If you are running a local Pokémon Showdown instance, make sure it is active. To start cerbottana, run:

    python3 app.py

To stop the execution, use the command `.kill` on PS (the first character might differ, depending on the configured `COMMAND_CHARACTER`) or just raise a `SIGINT` (`Ctrl + C`) in the console.
