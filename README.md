# cerbottana

[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Total Alerts](https://img.shields.io/lgtm/alerts/g/Parnassius/cerbottana.svg?logo=lgtm)](https://lgtm.com/projects/g/Parnassius/cerbottana/alerts)

Pokémon Showdown bot mainly used in the [Italiano room](https://play.pokemonshowdown.com/italiano).

## Contributing

Before submitting a PR, make sure your code is linted with ``pylint``, type-checked with ``mypy``, formatted with ``black`` and ``isort``.

The bulk of cerbottana's code are plugins (see [plugins reference](plugins/README.md)); working on a simple plugin is a good first contribution.

## Detailed install instructions

### Creating the virtual environment and installing dependencies

For these instruction we assume you're in the root directory of a cloned cerbottana repository. If you wish to test your bot instance locally you'll also need an active instance of a Pokemon Showdown server.

It's strongly recommended to use a Python virtual environment with Python 3.7; future versions should work too but might cause inconsistencies in `pip-compile` output. To create the virtual environment, run:

    python3 -m venv .venv

To activate it on Unix or MacOS:

    source .venv/bin/activate

To activate it on Windows:

    .venv\Scripts\activate.bat

If you just want to run an instance of the bot without dev-tools, add only the core dependencies:

    pip3 install -r requirements.txt

If you wish to contribute, you'll also need dev-tools; run the following command in addition to the previous one:

    pip3 install -r requirements-dev.txt

The next sections assume that you're still in the virtual environment. When you've finished, just run `deactivate` to exit it.

### Generating complementary files

Copy `.env-example` into `.env` and edit accordingly; optional environment variables are commented.

Use ``alembic`` to generate the required sqlite databases:

    alembic upgrade head

In the future if an update to your cerbottana fork changes the databases schemes you'll need to run this command again; to see if this is the case, just check if the ``alembic/`` folder has new files.

### Running a bot instance

Make sure the PS server you connect to is active if it's a local instance created for testing purposes. To start cerbottana:

    python3 app.py

To stop the execution, use the command `.kill` on PS (change the first character depending on the configured `COMMAND_CHARACTER`) or just raise a `SIGINT` (`Ctrl + C`) on the console.
