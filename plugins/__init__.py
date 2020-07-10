from typing import List

from os.path import dirname, basename, isfile, join
import glob
import importlib

from plugin_loader import Plugin


modules = glob.glob(join(dirname(__file__), "*.py"))

for f in modules:
    if isfile(f) and not f.endswith("__init__.py"):
        name = basename(f)[:-3]
        importlib.import_module("plugins." + name)

plugins = Plugin.get_all_commands()
