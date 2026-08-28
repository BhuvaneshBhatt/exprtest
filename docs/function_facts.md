# Function facts

`exprtest` uses a small registry of domain, sign, and value-class facts stated in
SymPy semantics. The active rules were audited against SymPy 1.14.0 documentation and
implementation behavior, and every retained fact has a regression test. The
optional SciPy compatibility job installs the current SciPy release so changes
in the two advertised counterparts are detected independently.

The registry is deliberately one-sided: a rule may provide a sufficient
condition without trying to characterize every point where a property holds.
`None` therefore means only that this bounded registry has no applicable proof.
Branch cuts are not treated as poles; a principal-branch value may remain
defined on a cut even when the function is discontinuous there.

| SymPy function | Facts used | Audited basis |
|---|---|---|
| `Abs` | integer, real, positive, nonnegative, defined | complex absolute value; nonnegative real output; positive for nonzero input |
| `acos` | real, positive, nonnegative, defined | principal inverse cosine; real range on `[-1, 1]` |
| `asin` | real, positive, negative, nonnegative, nonpositive, defined | principal inverse sine; real and sign-preserving on `[-1, 1]` |
| `atan` | real, positive, negative, nonnegative, nonpositive, defined | principal inverse tangent; real/sign-preserving on the real axis; singular at `±I` |
| `ceiling` | integer, real, positive, negative, nonnegative, nonpositive | real-input ceiling inequalities; complex inputs are not promoted to ordinary integers |
| `cos` | real, defined | entire cosine; real on real inputs |
| `cosh` | real, positive, nonnegative, defined | entire hyperbolic cosine; strictly positive on the real axis |
| `erf` | real, positive, negative, nonnegative, nonpositive, defined | entire error function; real, odd, and sign-preserving on the real axis |
| `erfc` | real, positive, nonnegative, defined | entire complementary error function; strictly positive on the real axis |
| `factorial` | integer, real, positive, nonnegative, defined | SymPy gamma continuation; poles at negative integers; positive for real `x > -1` |
| `floor` | integer, real, positive, negative, nonnegative, nonpositive | real-input floor inequalities; complex inputs are not promoted to ordinary integers |
| `gamma` | integer, real, positive, nonnegative, defined | meromorphic gamma; poles at nonpositive integers; positive on positive reals |
| `log` | real, positive, negative, nonnegative, nonpositive, defined | principal logarithm; nonzero complex domain; real/sign rules for positive real inputs |
| `loggamma` | real, positive, negative, nonnegative, nonpositive, defined | SymPy principal log-gamma continuation; poles at nonpositive integers; positive-real sign intervals |
| `sin` | real, defined | entire sine; real on real inputs |
| `sinc` | defined | SymPy unnormalized `sin(x)/x` with removable value `1` at zero |
| `sinh` | real, defined | entire hyperbolic sine; real on real inputs |
| `tan` | defined | meromorphic tangent; poles at `pi/2 + k*pi` |
| `tanh` | real, positive, negative, nonnegative, nonpositive, defined | meromorphic hyperbolic tangent; real/sign-preserving on reals; poles at `I*pi*(k + 1/2)` |
| `zeta` | real, positive, negative, nonnegative, nonpositive, defined | Riemann zeta continuation; sole pole at `1`; retained real sign intervals only |

## SciPy compatibility

The runtime registry does not depend on SciPy. `scipy.special.erf` and
`scipy.special.erfc` are documented as the same error and complementary error
functions for real or complex arguments, so they are recorded as compatible
counterparts.

`scipy.special.gamma` and `scipy.special.loggamma` are intentionally **not**
listed as exact behavioral counterparts. The mathematical functions agree on
ordinary points, but library-level boundary behavior differs: modern SciPy
returns IEEE `NaN`/signed infinities at gamma poles, and real-valued
`scipy.special.loggamma` inputs on the negative real axis return `NaN` while a
complex input can select the principal complex value. Those differences matter
for a registry concerned with definedness.

SymPy's `sinc` is the unnormalized `sin(x)/x` convention (with the removable
value `sinc(0) = 1`), so no SciPy/NumPy `sinc` counterpart is advertised.

The machine-readable inventory is in [`function_facts.csv`](function_facts.csv).
