# cerbottana

[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests status](https://img.shields.io/github/actions/workflow/status/Parnassius/cerbottana/ci-cd.yml?branch=main&label=tests)](https://github.com/Parnassius/cerbottana/actions/workflows/ci-cd.yml)
![Coverage](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FParnassius%2Fcerbottana%2Fcoverage-badge%2Fcoverage-badge.json)

cerbottana is a [Pokémon Showdown](https://play.pokemonshowdown.com/) bot, originally developed for the room [Italiano](https://play.pokemonshowdown.com/italiano).

## Getting started

These instructions assume you are in the root directory of a cloned cerbottana repository. If you use Windows, it is strongly advised to work within the [WSL](https://docs.microsoft.com/en-us/windows/wsl).

If you are going to test your bot locally, you will also need an active instance of a [Pokémon Showdown server](https://github.com/smogon/pokemon-showdown).

This project uses [uv](https://docs.astral.sh/uv/) to manage its dependencies, so you will need to install that as well.

### Generating complementary files

Copy `.env-example` into `.env` and edit the file accordingly. Optional environment variables are commented out.

### Running a bot instance

If you are running a local Pokémon Showdown instance, make sure it is active. Then, to start cerbottana, run:

    uv run cerbottana

To stop the execution just raise a `SIGINT` (`Ctrl + C`) in the console.

## Contributing

Before submitting a pull request, please make sure that `make` passes without errors.

The bulk of cerbottana code is plugins (see [plugins reference](src/cerbottana/plugins/README.md)). Working on a simple plugin is a good first contribution.
