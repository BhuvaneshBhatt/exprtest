"""Compatibility alias; shares implementation and caches with exprtools._numeric."""

import importlib as _importlib
import sys as _sys

_sys.modules[__name__] = _importlib.import_module("exprtools._numeric")
