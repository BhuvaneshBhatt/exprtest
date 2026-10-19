import subprocess
import sys

import sympy as sp
from exprtools._recurrence_families import RecurrenceFamilies
from exprtools.evidence import TransformationEvidence
from exprtools.recurrence import simplify_recurrences


def test_no_asymptotic_import_in_fresh_process():
    subprocess.run([sys.executable, '-c', '''
import sys
class Block:
    def find_spec(self, fullname, *args):
        if fullname == 'asymptotic' or fullname.startswith('asymptotic.'):
            raise AssertionError('unexpected host dependency')
sys.meta_path.insert(0, Block())
import sympy as s
from exprtools.recurrence import simplify_recurrences
x=s.Symbol('x',positive=True)
assert simplify_recurrences(s.gamma(x+2)/s.gamma(x)) == x*x+x
assert not any(n.startswith('asymptotic') for n in sys.modules)
'''], check=True)


def test_custom_heads_are_explicit_and_scoped():
    class Cylinder(sp.Function):
        nargs = 2
    n, z = sp.symbols('n z')
    expr = Cylinder(n+2,z)-z*Cylinder(n+1,z)+(n+1)*Cylinder(n,z)
    assert simplify_recurrences(expr) == expr
    families = RecurrenceFamilies(ParabolicCylinderD=Cylinder)
    assert simplify_recurrences(expr, families=families, budget_seconds=1) == 0
    assert simplify_recurrences(expr) == expr


def test_package_evidence_and_event_interface():
    x=sp.Symbol('x')
    events=[]
    result=simplify_recurrences(sp.gamma(x+2)/sp.gamma(x), return_result=True, record_event=events.append)
    assert events == ['recurrence_calls']
    assert result.steps == 2
    assert isinstance(result.evidence[0], TransformationEvidence)
    assert result.evidence[0].value == result.expression


def test_principal_powers_guards_and_budgets():
    a,z=sp.symbols('a z')
    e=sp.uppergamma(a+1,z)-a*sp.uppergamma(a,z)
    assert simplify_recurrences(e)==e
    assert simplify_recurrences(e,assumptions=sp.Ne(z,0))==z**a*sp.exp(-z)
    assert simplify_recurrences(e,assumptions=sp.Ne(z,0),budget_seconds=0)==e
