import glob
import importlib
from os.path import basename, dirname, isfile, join
from typing import List

from plugin_loader import Plugin

modules = glob.glob(join(dirname(__file__), "*.py"))

for f in modules:
    if isfile(f) and not f.endswith("__init__.py"):
        name = basename(f)[:-3]
        importlib.import_module("plugins." + name)

plugins = Plugin.get_all_commands()
