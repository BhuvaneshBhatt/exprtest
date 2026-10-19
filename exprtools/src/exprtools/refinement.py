"""Conservative assumption-aware refinement with its own rewrite rules.

Uses SymPy's predicate prover, never SymPy refine or its refine handlers. No
power denesting, forced logarithm splitting, or inferred numerical identities.
"""

import sympy as sp
from sympy.logic.boolalg import Boolean

from ._simplification_models import SimplificationBudget, SimplificationResult, _Run
from .context import is_defined, resolve_context
from .evidence import TransformationEvidence


def _rule(expr, context):
    q = context.proves
    if isinstance(expr, Boolean):
        value = context.truth(expr)
        if value is not None:
            return sp.true if value else sp.false, "condition"
    if not isinstance(expr, sp.Expr):
        return expr, None
    # Predicate proofs describe values where their arguments exist. They do
    # not prove that replacing im(1/x) by zero preserves the hole at x=0.
    if not is_defined(expr, context):
        return expr, None
    if expr.func in (
        sp.Abs,
        sp.sign,
        sp.arg,
        sp.re,
        sp.im,
        sp.conjugate,
        sp.floor,
        sp.ceiling,
    ):
        x = expr.args[0]
        if expr.func is sp.Abs:
            if q(sp.Q.zero(x)):
                return sp.S.Zero, "abs_zero"
            if q(sp.Q.nonnegative(x)):
                return x, "abs_nonnegative"
            if q(sp.Q.nonpositive(x)):
                return -x, "abs_nonpositive"
        if expr.func is sp.sign:
            if q(sp.Q.positive(x)):
                return sp.S.One, "sign_positive"
            if q(sp.Q.negative(x)):
                return sp.S.NegativeOne, "sign_negative"
            if q(sp.Q.zero(x)):
                return sp.S.Zero, "sign_zero"
        if expr.func is sp.arg:
            if q(sp.Q.positive(x)):
                return sp.S.Zero, "arg_positive"
            if q(sp.Q.negative(x)):
                return sp.pi, "arg_negative"
        if expr.func in (sp.re, sp.im, sp.conjugate):
            if q(sp.Q.real(x)):
                return (sp.S.Zero if expr.func is sp.im else x), "real_component"
            if q(sp.Q.imaginary(x)):
                value = {sp.re: sp.S.Zero, sp.im: -sp.I * x, sp.conjugate: -x}[
                    expr.func
                ]
                return value, "imaginary_component"
        if expr.func in (sp.floor, sp.ceiling) and q(sp.Q.integer(x)):
            return x, "integer_rounding"
    if expr.is_Pow:
        base, exponent = expr.args
        if base == -1:
            if q(sp.Q.even(exponent)):
                return sp.S.One, "even_parity"
            if q(sp.Q.odd(exponent)):
                return sp.S.NegativeOne, "odd_parity"
        if exponent == sp.S.Half and base.is_Pow:
            x, n = base.args
            if (
                n.is_Integer is True
                and n > 0
                and n % 2 == 0
                and q(sp.Q.real(x))
                and is_defined(x, context)
            ):
                absolute, _ = _rule(sp.Abs(x, evaluate=False), context)
                return absolute ** (n // 2), "real_even_root"
    if expr.func is sp.exp and expr.args[0].func is sp.log:
        logarithm = expr.args[0]
        if is_defined(logarithm, context):
            return logarithm.args[0], "exp_log_nonzero"
    if expr.func is sp.log:
        x = expr.args[0]
        if x.func is sp.exp and q(sp.Q.real(x.args[0])):
            return x.args[0], "log_exp_real"
        if x.is_Pow:
            b, e = x.args
            if (
                q(sp.Q.positive(b))
                and q(sp.Q.real(e))
                and is_defined(b, context)
                and is_defined(e, context)
            ):
                return e * sp.log(b), "log_positive_power"
    if expr.func in (sp.sin, sp.cos, sp.tan):
        n = expr.args[0].extract_multiplicatively(sp.pi)
        if n is not None and q(sp.Q.integer(n)):
            if expr.func in (sp.sin, sp.tan):
                return sp.S.Zero, "integer_pi"
            power = sp.Pow(-1, n, evaluate=False)
            value, _ = _rule(power, context)
            return value, "cos_integer_pi"
    return expr, None


def refine(expr, assumptions=True, *, context=None, budget=None, return_result=False):
    """Refine guarded scalar identities; unknown conditions leave nodes unchanged.

    Bound-variable constructs are left opaque. Piecewise branches are refined
    under their condition and negations of all preceding branch conditions.
    Budgets are cooperative and checked between nodes and rewrites.
    """
    original = sp.sympify(expr)
    context = resolve_context(context, assumptions)
    budget = SimplificationBudget() if budget is None else budget
    if not isinstance(budget, SimplificationBudget):
        raise TypeError("budget must be SimplificationBudget")
    run = _Run(budget)
    current = original

    def finish():
        result = SimplificationResult(
            original,
            current,
            tuple(run.evidence),
            run.steps,
            run.stopped,
            context.domain,
        )
        return result if return_result else current

    if sp.count_ops(original) > budget.max_ops:
        run.stopped = "input operation cap"
        return finish()
    if not run.available():
        return finish()
    if not context.consistent:
        run.stopped = "inconsistent assumptions"
        return finish()

    def record(before, after, method, local):
        if after == before or not run.available():
            return before
        if sp.count_ops(after) > budget.max_ops:
            run.stopped = "growth cap"
            return before
        run.steps += 1
        run.evidence.append(
            TransformationEvidence(
                "refine_" + method,
                "Guarded identity under "
                + str(local.assumptions)
                + "; principal branches and original definedness preserved.",
                ((before, after),),
                after,
            )
        )
        return after

    def walk(node, local):
        if not run.available() or not node.args:
            return node
        # Do not apply assumptions on a free symbol to a shadowed bound one.
        if isinstance(
            node,
            (
                sp.Integral,
                sp.Sum,
                sp.Product,
                sp.Lambda,
                sp.Derivative,
                sp.Limit,
                sp.Subs,
            ),
        ):
            return node
        start_steps, start_evidence = run.steps, len(run.evidence)

        def rollback():
            run.steps = start_steps
            del run.evidence[start_evidence:]
            return node

        if isinstance(node, sp.Piecewise):
            branches = []
            remaining = local
            for value, condition in node.args:
                if not run.available():
                    return rollback()
                truth = remaining.truth(condition)
                if truth is False:
                    remaining = remaining.with_assumptions(sp.Not(condition))
                    continue
                branch = remaining.with_assumptions(condition)
                refined = walk(value, branch) if branch.consistent else value
                branches.append((refined, sp.true if truth is True else condition))
                if truth is True:
                    break
                remaining = remaining.with_assumptions(sp.Not(condition))
            if branches:
                candidate = sp.Piecewise(*branches, evaluate=False)
                if not run.available():
                    return rollback()
                return record(node, candidate, "piecewise", local)
            return node
        args = tuple(walk(a, local) for a in node.args)
        rebuilt = node
        if args != node.args:
            try:
                rebuilt = node.func(*args, evaluate=False)
            except (TypeError, ValueError, NotImplementedError):
                return rollback()
        if not run.available():
            return rebuilt
        candidate, method = _rule(rebuilt, local)
        return record(rebuilt, candidate, method, local) if method else rebuilt

    seen = {current}
    while run.available():
        candidate = walk(current, context)
        if candidate == current:
            break
        current = candidate
        if current in seen:
            run.stopped = "cycle"
            break
        seen.add(current)
    return finish()
