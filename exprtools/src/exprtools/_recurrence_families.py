"""Curated exact recurrences over explicitly supplied function-head identities.

SymPy families are available by default. External packages bind their own heads
using RecurrenceFamilies; omitted roles are unavailable. No global registration,
function-name matching, or dependency on a limit engine is used.
"""
from dataclasses import dataclass
from typing import ClassVar
import sympy as sp

@dataclass(frozen=True)
class RecurrenceFamilies:
    """Adapter interface for curated function conventions and recurrence rules.

    Supply classes implementing the documented conventions of each named role.
    An adapter may subclass this provider to extend EXTRA_HEADS, TWO_BASIS,
    signatures, function_at and next_basis. next_basis must establish each new
    denominator through guard, or raise ValueError to refuse a transformation.
    Instances are per call; registration never mutates process-global state.
    """
    RegularizedHypergeometric0F1: object = None
    HypergeometricU: object = None
    KelvinBei: object = None
    KelvinBer: object = None
    KelvinKei: object = None
    KelvinKer: object = None
    LegendreQ: object = None
    ParabolicCylinderD: object = None
    RegularizedHypergeometric1F1: object = None
    RegularizedHypergeometric2F1: object = None
    StruveH: object = None
    StruveL: object = None
    WhittakerM: object = None
    WhittakerW: object = None

    POLYNOMIALS: ClassVar[tuple] = (
        sp.hermite,
        sp.hermite_prob,
        sp.chebyshevt,
        sp.chebyshevu,
        sp.legendre,
        sp.assoc_legendre,
        sp.laguerre,
        sp.assoc_laguerre,
        sp.gegenbauer,
        sp.jacobi,
    )

    @property
    def KELVIN(self):
        return tuple(h for h in (self.KelvinBer, self.KelvinBei, self.KelvinKer, self.KelvinKei) if h is not None)

    @property
    def EXTRA_HEADS(self):
        return tuple(h for h in (
    self.LegendreQ,
    *self.KELVIN,
    sp.Ynm,
    sp.lowergamma,
    sp.harmonic,
    sp.lerchphi,
    sp.factorial,
    sp.rf,
    sp.ff,
    sp.subfactorial,
    sp.bernoulli,
    sp.euler,
    self.StruveH,
    self.StruveL,
    self.RegularizedHypergeometric0F1,
    self.ParabolicCylinderD,
    self.HypergeometricU,
    self.WhittakerM,
    self.WhittakerW,
    self.RegularizedHypergeometric1F1,
    self.RegularizedHypergeometric2F1,
    *self.POLYNOMIALS,
    sp.hyper,
) if h is not None)

    @property
    def TWO_BASIS(self):
        return tuple(h for h in (
    self.LegendreQ,
    *self.KELVIN,
    sp.Ynm,
    self.ParabolicCylinderD,
    self.HypergeometricU,
    self.WhittakerM,
    self.WhittakerW,
    self.RegularizedHypergeometric1F1,
    self.RegularizedHypergeometric2F1,
    sp.subfactorial,
    *self.POLYNOMIALS,
    self.StruveH,
    self.StruveL,
    self.RegularizedHypergeometric0F1,
    sp.hyper,
) if h is not None)

    def signatures(self, atom):
        h = atom.func
        a = atom.args
        if h is sp.factorial or h is sp.subfactorial:
            return [((), a[0])]
        if h in (sp.rf, sp.ff):
            return [((a[0],), a[1])]
        if h in (sp.bernoulli, sp.euler):
            if len(a) != 2 or a[0].is_Integer is not True or not 0 <= a[0] <= 16:
                return []
            return [((a[0],), a[1])]
        if h in (self.HypergeometricU, self.RegularizedHypergeometric1F1):
            return [(("a", a[1], a[2]), a[0]), (("b", a[0], a[2]), a[1])]
        if h is self.RegularizedHypergeometric2F1:
            return [
                ((a[1], a[2], a[3]), a[0]),
                ((a[0], a[2], a[3]), a[1]),
                (("c", a[0], a[1], a[3]), a[2]),
            ]
        if h is sp.harmonic:
            return [((a[1] if len(a) == 2 else sp.S.One,), a[0])]
        if h is sp.lerchphi:
            return [((a[0], a[1]), a[2])]
        if h in self.POLYNOMIALS:
            return [(a[1:], a[0])]
        if h is sp.hyper:
            upper, lower, z = a
            if len(lower) != 1:
                return []
            b = lower[0]
            if len(upper) == 0:
                return [(("0f1", z), b)]
            if len(upper) == 1:
                return [(("1f1_a", b, z), upper[0]), (("1f1_b", upper[0], z), b)]
            if len(upper) == 2:
                # SymPy sorts the upper parameters. Match either slot so that a
                # harmless sorting permutation does not change congruence groups.
                return [
                    (("2f1_a", upper[1], b, z), upper[0]),
                    (("2f1_a", upper[0], b, z), upper[1]),
                    (("2f1_c", *upper, z), b),
                ]
            return []
        return [(a[1:], a[0])]


    def function_at(self, head, key, parameter):
        if head is self.RegularizedHypergeometric2F1 and key[0] == "c":
            return head(key[1], key[2], parameter, key[3])
        if head in (self.HypergeometricU, self.RegularizedHypergeometric1F1):
            return (
                head(parameter, key[1], key[2])
                if key[0] == "a"
                else head(key[1], parameter, key[2])
            )
        if head in (sp.rf, sp.ff, sp.bernoulli, sp.euler):
            return head(*key, parameter, evaluate=False)
        if head is not sp.hyper:
            return head(parameter, *key, evaluate=False)
        kind = key[0]
        if kind == "0f1":
            return sp.hyper((), (parameter,), key[1])
        if kind == "1f1_a":
            return sp.hyper((parameter,), (key[1],), key[2])
        if kind == "1f1_b":
            return sp.hyper((key[1],), (parameter,), key[2])
        if kind == "2f1_c":
            return sp.hyper((key[1], key[2]), (parameter,), key[3])
        return sp.hyper((parameter, key[1]), (key[2],), key[3])


    def next_basis(self, head, key, a0, k, basis, guard):
        """Return one upward step, raising ValueError if a denominator is unproved."""
        p = a0 + k - 1

        def divide(num, den):
            if not guard(den):
                raise ValueError("unresolved denominator")
            return num / den

        if head is sp.factorial:
            return (p + 1) * basis[k - 1]
        if head is sp.rf:
            return (key[0] + p) * basis[k - 1]
        if head is sp.ff:
            return (key[0] - p) * basis[k - 1]
        if head is sp.bernoulli:
            return basis[k - 1] + (key[0] * p ** (key[0] - 1) if key[0] else 0)
        if head is sp.euler:
            return 2 * p ** key[0] - basis[k - 1]
        if head is sp.lowergamma:
            z = key[0]
            if not guard(z):
                raise ValueError("zero argument")
            return p * basis[k - 1] - z**p * sp.exp(-z)
        if head is sp.harmonic:
            if not guard(a0 + k):
                raise ValueError("harmonic pole")
            return basis[k - 1] + (a0 + k) ** (-key[0])
        if head is sp.lerchphi:
            z, s = key
            return divide(basis[k - 1] - p ** (-s), z)
        if k == 1:
            return self.function_at(head, key, a0 + 1)
        left, middle = basis[k - 2], basis[k - 1]
        if head is sp.subfactorial:
            return p * (middle + left)
        if head is sp.Ynm:
            m, theta, phi = key
            high = sp.sqrt(((p + 1) ** 2 - m**2) / ((2 * p + 1) * (2 * p + 3)))
            low = sp.sqrt((p**2 - m**2) / ((2 * p - 1) * (2 * p + 1)))
            return divide(sp.cos(theta) * middle - low * left, high)
        if head in self.KELVIN:
            z = key[0]
            real, imag = (
                (self.KelvinBer, self.KelvinBei)
                if head in (self.KelvinBer, self.KelvinBei)
                else (self.KelvinKer, self.KelvinKei)
            )
            R = {0: real(a0, z), 1: real(a0 + 1, z)}
            image = {0: imag(a0, z), 1: imag(a0 + 1, z)}
            for j in range(2, k + 1):
                c = divide(sp.sqrt(2) * (a0 + j - 1), z)
                R[j] = -R[j - 2] - c * (R[j - 1] - image[j - 1])
                image[j] = -image[j - 2] - c * (R[j - 1] + image[j - 1])
            return R[k] if head is real else image[k]
        if head is self.ParabolicCylinderD:
            return key[0] * middle - p * left
        if head is self.LegendreQ:
            m, z = key
            return divide((2 * p + 1) * z * middle - (p + m) * left, p - m + 1)
        if head in (self.WhittakerM, self.WhittakerW):
            mu, z = key
            if head is self.WhittakerM:
                return divide(
                    (mu - p + sp.Rational(1, 2)) * left + (2 * p - z) * middle,
                    mu + p + sp.Rational(1, 2),
                )
            return (mu**2 - (p - sp.Rational(1, 2)) ** 2) * left + (z - 2 * p) * middle
        if head is self.HypergeometricU:
            fixed, z = key[1:]
            if key[0] == "a":
                return divide((2 * p + z - fixed) * middle - left, p * (p - fixed + 1))
            return divide((p + z - 1) * middle - (p - fixed - 1) * left, z)
        if head is self.RegularizedHypergeometric1F1:
            fixed, z = key[1:]
            if key[0] == "a":
                return divide((fixed - p) * left + (2 * p - fixed + z) * middle, p)
            return divide(left + (1 - p - z) * middle, z * (fixed - p))
        if head is self.RegularizedHypergeometric2F1:
            if key[0] == "c":
                a, b, z = key[1:]
                return divide(
                    (1 - z) * left - (p - 1 - (2 * p - a - b - 1) * z) * middle,
                    (p - a) * (p - b) * z,
                )
            b, c, z = key
            return divide((c - p) * left + (2 * p - c + (b - p) * z) * middle, p * (1 - z))
        if head in (sp.hermite, sp.hermite_prob):
            return (2 if head is sp.hermite else 1) * (key[0] * middle - p * left)
        if head in (sp.chebyshevt, sp.chebyshevu):
            return 2 * key[0] * middle - left
        if head is sp.legendre:
            return divide((2 * p + 1) * key[0] * middle - p * left, p + 1)
        if head is sp.assoc_legendre:
            m, z = key
            return divide((2 * p + 1) * z * middle - (p + m) * left, p - m + 1)
        if head in (sp.laguerre, sp.assoc_laguerre):
            alpha, z = (sp.S.Zero, key[0]) if head is sp.laguerre else key
            return divide((2 * p + alpha + 1 - z) * middle - (p + alpha) * left, p + 1)
        if head is sp.gegenbauer:
            alpha, z = key
            return divide(2 * (p + alpha) * z * middle - (p + 2 * alpha - 1) * left, p + 1)
        if head is sp.jacobi:
            a, b, z = key
            t = 2 * p + a + b
            return divide(
                (t + 1) * (t * (t + 2) * z + a * a - b * b) * middle
                - 2 * (p + a) * (p + b) * (t + 2) * left,
                2 * (p + 1) * (p + a + b + 1) * t,
            )
        if head in (self.StruveH, self.StruveL):
            z = key[0]
            # Use the same principal power (z/2)**p; never split complex powers.
            source = (z / 2) ** p / (sp.sqrt(sp.pi) * sp.gamma(p + sp.Rational(3, 2)))
            term = divide(2 * p * middle, z) + source
            return term - left if head is self.StruveH else left - term
        if head is self.RegularizedHypergeometric0F1:
            return divide(left - p * middle, key[0])
        kind = key[0]
        if kind == "0f1":
            return divide(p * (p - 1) * (left - middle), key[1])
        if kind == "1f1_a":
            b, z = key[1:]
            return divide((b - p) * left + (2 * p - b + z) * middle, p)
        if kind == "1f1_b":
            a, z = key[1:]
            return divide(p * (p - 1) * left + p * (1 - p - z) * middle, z * (a - p))
        if kind == "2f1_c":
            a, b, z = key[1:]
            return divide(
                p * (p - 1) * (1 - z) * left
                - p * (p - 1 - (2 * p - a - b - 1) * z) * middle,
                (p - a) * (p - b) * z,
            )
        b, c, z = key[1:]
        return divide((c - p) * left + (2 * p - c + (b - p) * z) * middle, p * (1 - z))

DEFAULT_FAMILIES = RecurrenceFamilies()
