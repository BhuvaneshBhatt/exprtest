"""Compatibility alias; shares implementation and caches with exprtools._transcendental."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module("exprtools._transcendental")
