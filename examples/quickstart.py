"""Small executable demonstration of the public exprtest API."""

import sympy as sp

from exprtest import is_algebraic, is_prime, profile_zerotest, zerotest


def main() -> None:
    x = sp.symbols("x")

    assert zerotest(0) is True
    assert zerotest(sp.pi) is False
    assert zerotest(sp.Function("f")(x)) is None
    assert is_prime(97) is True
    assert is_algebraic(sp.sqrt(2)) is True
    assert is_algebraic(sp.pi) is False

    profile = profile_zerotest(sp.exp(sp.sqrt(2), evaluate=False))
    assert profile.result is False
    print("proof-aware zero testing and numeric predicates are available")


if __name__ == "__main__":
    main()
