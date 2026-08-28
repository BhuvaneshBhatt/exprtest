import sympy as sp

from exprtest import (
    ElementOf,
    is_algebraic,
    is_integer,
    is_prime,
    is_rational,
    is_real,
    number_kind,
)
from exprtest._domains import Algebraics, NumberKind


def test_existing_domain_api_is_public():
    assert number_kind(sp.sqrt(2)) is NumberKind.ALGEBRAIC
    assert ElementOf(sp.sqrt(2), Algebraics) is True


def test_integer_predicate():
    assert is_integer(sp.Integer(7)) is True
    assert is_integer(sp.Rational(3, 2)) is False
    assert is_integer(sp.pi) is False


def test_rational_predicate():
    assert is_rational(sp.Rational(3, 2)) is True
    assert is_rational(sp.sqrt(2)) is False
    assert is_rational(sp.pi) is False


def test_real_predicate():
    assert is_real(sp.sqrt(2)) is True
    assert is_real(sp.pi) is True
    assert is_real(sp.I) is False


def test_algebraic_predicate():
    assert is_algebraic(sp.sqrt(2)) is True
    assert is_algebraic(sp.I) is True
    assert is_algebraic(sp.pi) is False


def test_prime_predicate():
    assert is_prime(sp.Integer(2)) is True
    assert is_prime(sp.Integer(97)) is True
    assert is_prime(sp.Integer(1)) is False
    assert is_prime(sp.Integer(-7)) is False
    assert is_prime(sp.Integer(91)) is False
    assert is_prime(sp.Rational(3, 2)) is False
    assert is_prime(sp.pi) is False


def test_predicates_use_assumptions():
    n = sp.symbols("n")
    assert is_integer(n, sp.Q.integer(n)) is True
    assert is_real(n, sp.Q.real(n)) is True
    assert is_prime(n, sp.Q.prime(n)) is True
