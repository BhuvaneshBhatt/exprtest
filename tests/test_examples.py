import runpy
from pathlib import Path


def test_quickstart_example_runs(capsys):
    """The checked-in quick-start example should execute without modification."""
    path = Path(__file__).parents[1] / "examples" / "quickstart.py"
    runpy.run_path(str(path), run_name="__main__")
    output = capsys.readouterr().out
    assert "proof-aware zero testing" in output
