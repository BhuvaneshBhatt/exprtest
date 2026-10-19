"""Old and new imports must share types, mutable state, and pickle paths."""
import importlib
import pickle
from pathlib import Path

import exprtest
import exprtools


def test_public_objects_are_identical():
    for name in exprtest.__all__:
        assert getattr(exprtest, name) is getattr(exprtools, name)


def test_all_legacy_submodules_alias_the_implementation():
    for path in Path(exprtest.__file__).parent.glob('*.py'):
        if path.stem != '__init__':
            assert importlib.import_module('exprtest.' + path.stem) is importlib.import_module('exprtools.' + path.stem)


def test_old_result_pickle_path_resolves():
    # Protocol-0 GLOBAL references from the old package stay loadable.
    assert pickle.loads(b'cexprtest._result\nVerdict\n.') is exprtools.Verdict
