"""Explicit scalar mathematical contexts, independent of SymPy's global assumptions."""

from dataclasses import dataclass, field, replace
from functools import cached_property

import sympy as sp
from sympy.assumptions import AssumptionsContext
from sympy.assumptions.assume import AppliedPredicate
from sympy.logic.boolalg import Boolean


def _predicates(condition):
    if isinstance(condition, sp.Equality):
        return sp.Q.zero(condition.lhs - condition.rhs)
    if isinstance(condition, sp.Unequality):
        return ~sp.Q.zero(condition.lhs - condition.rhs)
    if isinstance(condition, sp.StrictGreaterThan):
        return sp.Q.positive(condition.lhs - condition.rhs)
    if isinstance(condition, sp.StrictLessThan):
        return sp.Q.negative(condition.lhs - condition.rhs)
    if isinstance(condition, sp.GreaterThan):
        return sp.Q.nonnegative(condition.lhs - condition.rhs)
    if isinstance(condition, sp.LessThan):
        return sp.Q.nonpositive(condition.lhs - condition.rhs)
    if condition.func in (sp.And, sp.Or, sp.Not, sp.Implies, sp.Equivalent, sp.Xor):
        return condition.func(*map(_predicates, condition.args))
    return condition


def _linear_relation(predicate):
    if isinstance(predicate, AppliedPredicate) and len(predicate.arguments) == 1:
        x = predicate.arguments[0]
        relations = {
            sp.Q.positive: lambda: x > 0,
            sp.Q.negative: lambda: x < 0,
            sp.Q.nonnegative: lambda: x >= 0,
            sp.Q.nonpositive: lambda: x <= 0,
            sp.Q.zero: lambda: sp.Eq(x, 0),
        }
        return (
            relations[predicate.function]() if predicate.function in relations else None
        )
    if getattr(predicate, "is_Relational", False):
        return predicate
    return predicate if predicate in (sp.true, sp.false) else None


def _linear_formula(assumptions):
    clauses = tuple(_linear_relation(c) for c in sp.And.make_args(assumptions))
    if any(c is None for c in clauses):
        return None
    formula = sp.And(*clauses)
    if sp.count_ops(formula) > 64:
        return None
    for relation in formula.atoms(sp.core.relational.Relational):
        difference = relation.lhs - relation.rhs
        symbols = tuple(difference.free_symbols)
        if not symbols:
            continue
        try:
            poly = sp.Poly(difference, *symbols)
            if poly.total_degree() > 1 or not all(c.is_Rational for c in poly.coeffs()):
                return None
        except sp.PolynomialError:
            return None
    return formula


def _linear_unsat(formula):
    try:
        return sp.satisfiable(formula, use_lra_theory=True) is False
    except (ValueError, TypeError, AssertionError, NotImplementedError):
        # SymPy 1.12 has no LRA satisfiable option. Exact one-variable affine
        # interval intersections provide a conservative independent fallback.
        domains = {}
        for relation in sp.And.make_args(formula):
            if relation is sp.false:
                return True
            if not getattr(relation, "is_Relational", False):
                continue
            difference = relation.lhs - relation.rhs
            symbols = tuple(difference.free_symbols)
            if len(symbols) != 1:
                continue
            x = symbols[0]
            try:
                p = sp.Poly(difference, x)
            except sp.PolynomialError:
                continue
            if p.degree() != 1 or not all(c.is_Rational for c in p.all_coeffs()):
                continue
            a, b = p.all_coeffs()
            root = -b / a
            op = relation.rel_op
            if a < 0:
                op = {
                    ">": "<",
                    ">=": "<=",
                    "<": ">",
                    "<=": ">=",
                    "==": "==",
                    "!=": "!=",
                }[op]
            interval = {
                ">": lambda root=root: sp.Interval.open(root, sp.oo),
                ">=": lambda root=root: sp.Interval(root, sp.oo),
                "<": lambda root=root: sp.Interval.open(-sp.oo, root),
                "<=": lambda root=root: sp.Interval(-sp.oo, root),
                "==": lambda root=root: sp.FiniteSet(root),
                "!=": lambda root=root: sp.Complement(sp.S.Reals, sp.FiniteSet(root)),
            }[op]()
            domains[x] = domains.get(x, sp.S.Reals).intersect(interval)
            if domains[x] is sp.S.EmptySet:
                return True
        return False


def _ask(predicate, assumptions=sp.true):
    # A fresh context excludes ambient global_assumptions from every query.
    try:
        return sp.ask(predicate, assumptions, context=AssumptionsContext())
    except (ValueError, TypeError, NotImplementedError):
        return None


@dataclass(frozen=True)
class MathematicalContext:
    """Finite complex scalar variables with explicit local assumptions.

    pointwise preserves definedness; common admits identities on the original
    common domain and retains the original expression in results; germ admits
    the recurrence engine's guarded punctured real one-variable identities.
    Unsupported assumptions are inconclusive, never numerical evidence.
    """

    assumptions: object = sp.true
    domain: str = "pointwise"
    variables: tuple = ()
    target: tuple = ()
    _queries: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        assumptions = sp.sympify(self.assumptions)
        if not isinstance(assumptions, Boolean):
            raise TypeError("assumptions must be Boolean")
        if self.domain not in ("pointwise", "common", "germ"):
            raise ValueError("domain must be pointwise, common, or germ")
        variables = (
            (self.variables,)
            if isinstance(self.variables, sp.Symbol)
            else tuple(self.variables)
        )
        target = (
            (self.target,)
            if isinstance(self.target, (sp.Basic, int, float))
            else tuple(self.target)
        )
        target = tuple(sp.sympify(p) for p in target)
        if any(not isinstance(x, sp.Symbol) for x in variables):
            raise TypeError("variables must be symbols")
        if len(variables) != len(target):
            raise ValueError("variables and target must have equal lengths")
        if self.domain == "germ" and (
            len(variables) != 1
            or variables[0].is_real is not True
            or target[0].is_extended_real is not True
        ):
            raise ValueError(
                "germ contexts need one real symbol and a real extended target"
            )
        object.__setattr__(self, "assumptions", assumptions)
        object.__setattr__(self, "variables", variables)
        object.__setattr__(self, "target", target)

    @cached_property
    def predicate_assumptions(self):
        predicates = _predicates(self.assumptions)
        # Include known intrinsic facts so explicit contradictory assumptions
        # cannot override a symbol's declared properties in ask().
        facts = []
        for symbol in predicates.free_symbols:
            for name in (
                "positive",
                "negative",
                "zero",
                "real",
                "integer",
                "finite",
                "even",
                "odd",
            ):
                value = getattr(symbol, "is_" + name, None)
                if value is not None:
                    fact = getattr(sp.Q, name)(symbol)
                    facts.append(fact if value else ~fact)
        return sp.And(predicates, *facts)

    @cached_property
    def consistent(self):
        assumptions = self.predicate_assumptions
        if assumptions is sp.false:
            return False
        linear = _linear_formula(self.assumptions)
        if linear is not None and _linear_unsat(linear):
            return False
        # Substitute properties already disproved by intrinsic expression facts.
        known = {}
        for predicate in assumptions.atoms(AppliedPredicate):
            value = _ask(predicate)
            if value is not None:
                known[predicate] = sp.true if value else sp.false
        simplified = assumptions.xreplace(known)
        if simplified is sp.false or sp.satisfiable(simplified) is False:
            return False
        for predicate in assumptions.atoms(AppliedPredicate):
            try:
                sp.ask(predicate, assumptions, context=AssumptionsContext())
            except ValueError:
                return False
            except (TypeError, NotImplementedError):
                pass
        # Intrinsic properties of context-refined symbols also expose affine
        # contradictions such as x < 0 together with x - 1 > 0.
        replacements = {}
        for predicate in assumptions.atoms(AppliedPredicate):
            value = _ask(predicate.xreplace(self.refined_symbols))
            if value is not None:
                replacements[predicate] = sp.true if value else sp.false
        if sp.satisfiable(assumptions.xreplace(replacements)) is False:
            return False
        return True

    @cached_property
    def refined_symbols(self):
        mapping = {}
        for symbol in self.predicate_assumptions.free_symbols:
            facts = {}
            for name in (
                "positive",
                "negative",
                "nonnegative",
                "nonpositive",
                "real",
                "imaginary",
                "integer",
                "even",
                "odd",
                "zero",
                "finite",
            ):
                value = _ask(getattr(sp.Q, name)(symbol), self.predicate_assumptions)
                if value is True or (name == "zero" and value is False):
                    facts[name] = value
            if facts:
                try:
                    mapping[symbol] = sp.Dummy("context", **facts)
                except ValueError:
                    pass
        return mapping

    def query(self, predicate):
        if not self.consistent:
            return None
        predicate = sp.sympify(predicate)
        if predicate not in self._queries:
            value = _ask(predicate, self.predicate_assumptions)
            if value is None and self.refined_symbols:
                value = _ask(predicate.xreplace(self.refined_symbols))
            if value is None:
                relation = _linear_relation(predicate)
                linear = _linear_formula(self.assumptions)
                if (
                    relation is not None
                    and linear is not None
                    and _linear_formula(relation) is not None
                ):
                    if _linear_unsat(sp.And(linear, sp.Not(relation))):
                        value = True
                    elif _linear_unsat(sp.And(linear, relation)):
                        value = False
            self._queries[predicate] = value
        return self._queries[predicate]

    def proves(self, predicate):
        return self.query(predicate) is True

    def truth(self, condition):
        condition = sp.sympify(condition)
        if not self.consistent:
            return None
        if condition is sp.true:
            return True
        if condition is sp.false:
            return False
        if getattr(condition, "is_Relational", False) and not all(
            is_defined(arg, self) for arg in condition.args
        ):
            return None
        if isinstance(condition, AppliedPredicate) and not all(
            is_defined(arg, self) for arg in condition.arguments
        ):
            return None
        clauses = sp.And.make_args(self.assumptions)
        if condition in clauses:
            return True
        if sp.Not(condition) in clauses:
            return False
        if condition.func is sp.Not:
            value = self.truth(condition.args[0])
            return None if value is None else not value
        if condition.func in (sp.And, sp.Or):
            values = [self.truth(c) for c in condition.args]
            if condition.func is sp.And:
                return (
                    False
                    if False in values
                    else True
                    if all(v is True for v in values)
                    else None
                )
            return (
                True
                if True in values
                else False
                if all(v is False for v in values)
                else None
            )
        predicate = _predicates(condition)
        return self.query(predicate)

    def with_assumptions(self, assumptions):
        return replace(
            self,
            assumptions=sp.And(self.assumptions, sp.sympify(assumptions)),
            _queries={},
        )

    @cached_property
    def recurrence_assumptions(self):
        clauses = list(sp.And.make_args(self.assumptions))
        for p in self.assumptions.atoms(AppliedPredicate):
            if len(p.arguments) != 1:
                continue
            x = p.arguments[0]
            if p.function == sp.Q.positive:
                clauses.append(x > 0)
            elif p.function == sp.Q.negative:
                clauses.append(x < 0)
            elif p.function == sp.Q.nonzero:
                clauses.append(sp.Ne(x, 0))
        return sp.And(*clauses)


def resolve_context(context=None, assumptions=True):
    if context is None:
        return MathematicalContext(assumptions=assumptions)
    if not isinstance(context, MathematicalContext):
        raise TypeError("context must be MathematicalContext")
    return (
        context
        if sp.sympify(assumptions) is sp.true
        else context.with_assumptions(assumptions)
    )


def is_defined(expr, context):
    """Conservative sufficient test for finite values over an entire context.

    This deliberately refuses opaque functions and unresolved denominators.
    It is not a general singularity solver. Symbols range over finite scalars.
    """
    expr = sp.sympify(expr)
    if expr.has(sp.nan, sp.zoo, sp.oo, -sp.oo):
        return False
    if expr.is_number and expr.is_finite is True:
        return True
    if isinstance(expr, sp.Symbol):
        return (
            expr.is_infinite is not True
            and context.query(sp.Q.finite(expr)) is not False
        )
    if not isinstance(expr, sp.Expr) or not all(
        is_defined(a, context) for a in expr.args
    ):
        return False
    if expr.is_Add or expr.is_Mul:
        return True
    if expr.is_Pow:
        b, e = expr.args
        return (
            (context.proves(sp.Q.integer(e)) and context.proves(sp.Q.nonnegative(e)))
            or context.proves(sp.Q.positive(e))
            or context.query(sp.Q.zero(b)) is False
        )
    if expr.func in (
        sp.exp,
        sp.sin,
        sp.cos,
        sp.sinh,
        sp.cosh,
        sp.erf,
        sp.erfc,
        sp.Abs,
        sp.re,
        sp.im,
        sp.conjugate,
        sp.sign,
    ):
        return True
    if expr.func is sp.tan:
        return context.query(sp.Q.zero(sp.cos(expr.args[0]))) is False
    if expr.func in (sp.log, sp.arg):
        return context.query(sp.Q.zero(expr.args[0])) is False
    if expr.func in (sp.floor, sp.ceiling):
        return context.proves(sp.Q.real(expr.args[0]))
    if expr.func is sp.gamma:
        return context.proves(sp.Q.positive(expr.args[0]))
    if expr.func is sp.polygamma:
        m, z = expr.args
        return m.is_Integer is True and m >= 0 and context.proves(sp.Q.positive(z))
    if expr.func in (
        sp.besselj,
        sp.bessely,
        sp.besseli,
        sp.besselk,
        sp.hankel1,
        sp.hankel2,
    ):
        return context.query(sp.Q.zero(expr.args[1])) is False
    if expr.func is sp.uppergamma:
        return context.query(sp.Q.zero(expr.args[1])) is False
    if expr.func is sp.zeta and len(expr.args) == 2:
        s, a = expr.args
        return (
            context.proves(sp.Q.positive(a))
            and context.query(sp.Q.zero(s - 1)) is False
        )
    return False
