from typing import List, Set

from os.path import dirname, basename, isfile, join
import glob
import importlib

from handler_loader import Handler


modules = glob.glob(join(dirname(__file__), "*.py"))

for f in modules:
    if isfile(f) and not f.endswith("__init__.py"):
        name = basename(f)[:-3]
        importlib.import_module("handlers." + name)

handlers = Handler.get_all_handlers()
